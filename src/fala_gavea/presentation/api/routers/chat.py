from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort
from fala_gavea.presentation.api.dependencies import (
    get_llm_client,
    get_report_repo,
    get_semantic_search_port,
    require_any_role,
)
from fala_gavea.presentation.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
_log = logging.getLogger(__name__)


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
