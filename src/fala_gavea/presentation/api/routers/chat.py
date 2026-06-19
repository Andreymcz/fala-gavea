from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import OllamaUnavailableError
from fala_gavea.infrastructure.ollama.ollama_client import OllamaClient
from fala_gavea.presentation.api.dependencies import get_current_user

router = APIRouter()

_ollama_client: OllamaClient | None = None


def _get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
def nl_chat(
    body: ChatRequest,
    _current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Send messages to the Ollama NL assistant.

    Returns HTTP 503 when FALA_GAVEA_OLLAMA_URL is not configured.
    """
    client = _get_ollama_client()
    try:
        reply = client.chat(body.messages)
    except OllamaUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NL chat is unavailable in this deployment.",
        ) from exc
    return ChatResponse(reply=reply)
