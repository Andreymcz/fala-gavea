from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag
from fala_gavea.application.use_cases.help.answer_help_with_rag import AnswerHelpWithRag
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import OllamaUnavailableError
from fala_gavea.domain.repositories.doc_ports import IDocSearchPort
from fala_gavea.domain.repositories.filter_ports import ParseError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_doc_search_port,
    get_filter_parser,
    get_llm_client,
    get_report_repo,
    get_report_type_repo,
    get_semantic_search_port,
    require_any_role,
)
from fala_gavea.presentation.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitedDocResponse,
    HelpChatRequest,
    HelpChatResponse,
)
from fala_gavea.presentation.schemas.nl_filter import NLFilterRequest, NLFilterResponse

# Role -> document visibility levels. Default-deny: unknown roles fall back to
# ["public"] in the handler (see _ROLE_VISIBILITY.get(..., ["public"])).
_ROLE_VISIBILITY = {
    "citizen": ["public"],
    "agent": ["public"],
    "admin": ["public", "internal"],
}

router = APIRouter()
_log = logging.getLogger(__name__)

limiter = Limiter(
    key_func=lambda request: str(
        getattr(request.state, "current_user_id", None) or get_remote_address(request)
    )
)


@router.post("/chat", response_model=ChatResponse)
def nl_chat(
    body: ChatRequest,
    _current_user: User = Depends(require_any_role("agent", "admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
    llm_client: ILLMClient | None = Depends(get_llm_client),
) -> ChatResponse:
    if llm_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider is not configured.",
        )
    if search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is not available.",
        )
    use_case = AnswerWithRag(search_port, report_repo, llm_client)
    result = use_case.execute(body.message)
    return ChatResponse(response=result.response, cited_report_ids=result.cited_report_ids)


@router.post("/help", response_model=HelpChatResponse)
@limiter.limit("20/minute")
def nl_help(
    request: Request,
    body: HelpChatRequest,
    current_user: User = Depends(get_current_user),
    search_port: IDocSearchPort | None = Depends(get_doc_search_port),
    llm_client: ILLMClient | None = Depends(get_llm_client),
) -> HelpChatResponse:
    if llm_client is None or search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O assistente de ajuda está indisponível no momento.",
        )
    roles = _ROLE_VISIBILITY.get(current_user.role.value, ["public"])  # default-deny
    # SEJA "meta mode" (D-017): only admins get the SEJA-taxonomy/SDLC framing.
    # Resolved here in the router from the role (T2) — the use case stays auth-agnostic.
    meta_mode = current_user.role.value == "admin"
    result = AnswerHelpWithRag(search_port, llm_client).execute(
        body.message, roles=roles, meta_mode=meta_mode
    )
    return HelpChatResponse(
        response=result.response,
        cited_docs=[
            CitedDocResponse(
                source_path=c.source_path,
                section_title=c.section_title,
                score=c.score,
                doc_type=c.doc_type,
            )
            for c in result.cited_docs
        ],
    )


def _to_workspace_filters(body: dict) -> tuple[dict, list[str]]:
    """Adapt the parser's generic shape to the SPA's draft-filter shape.

    The parser emits multi-value facets (``report_type_ids``/``urgencies``/
    ``statuses``) plus ``q``/``text``, but the workspace store models a single
    value per facet (``type_id``/``urgency``/``status``/``semanticQuery``). We
    collapse each list to its first item and warn when extra values are dropped
    so the user knows only part of the request was applied.
    """
    out: dict = {}
    warnings: list[str] = []

    def take_first(src_key: str, dst_key: str, label: str) -> None:
        val = body.get(src_key)
        items = val if isinstance(val, list) else [val] if val else []
        if not items:
            return
        out[dst_key] = items[0]
        if len(items) > 1:
            warnings.append(f"{label}: apenas o primeiro valor foi aplicado ({items[0]}).")

    take_first("report_type_ids", "type_id", "Tipo de relato")
    take_first("urgencies", "urgency", "Urgência")
    take_first("statuses", "status", "Status")
    if body.get("since"):
        out["since"] = body["since"]
    if body.get("until"):
        out["until"] = body["until"]
    # Both semantic (q) and textual (text) search collapse to the single field.
    semantic = body.get("q") or body.get("text")
    if semantic:
        out["semanticQuery"] = semantic
    return out, warnings


@router.post("/filter", response_model=NLFilterResponse)
@limiter.limit("20/minute")
def nl_filter(
    request: Request,
    body: NLFilterRequest,
    _current_user: User = Depends(require_any_role("agent", "admin", "citizen")),
    filter_parser=Depends(get_filter_parser),
    report_type_repo=Depends(get_report_type_repo),
) -> NLFilterResponse:
    use_case = ParseNLFilter(filter_parser, report_type_repo)
    try:
        result = use_case.execute(body.text)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O assistente de filtros demorou muito para responder.",
        )
    except (OllamaUnavailableError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O assistente de filtros está indisponível no momento.",
        )
    except ParseError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível interpretar o filtro.",
        )
    mapped, collapse_warnings = _to_workspace_filters(result.body)
    return NLFilterResponse(body=mapped, warnings=result.warnings + collapse_warnings)
