from __future__ import annotations
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    cited_report_ids: list[str]


class HelpChatRequest(BaseModel):
    message: str


class CitedDocResponse(BaseModel):
    source_path: str
    section_title: str
    score: float


class HelpChatResponse(BaseModel):
    response: str
    cited_docs: list[CitedDocResponse]
