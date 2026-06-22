from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.filter_ports import ParseError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort
from fala_gavea.presentation.api.dependencies import (
    get_filter_parser,
    get_llm_client,
    get_report_repo,
    get_semantic_search_port,
    require_any_role,
)
from fala_gavea.presentation.schemas.chat import ChatRequest, ChatResponse
from fala_gavea.presentation.schemas.nl_filter import NLFilterRequest, NLFilterResponse

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


@router.post("/filter", response_model=NLFilterResponse)
@limiter.limit("20/minute")
def nl_filter(
    request: Request,
    body: NLFilterRequest,
    _current_user: User = Depends(require_any_role("agent", "admin", "citizen")),
    filter_parser=Depends(get_filter_parser),
) -> NLFilterResponse:
    use_case = ParseNLFilter(filter_parser)
    try:
        result = use_case.execute(body.text)
    except ParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse filter: {exc.message}",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    return NLFilterResponse(body=result.body, warnings=result.warnings)
