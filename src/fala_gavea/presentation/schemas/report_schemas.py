from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class ReportCreate(BaseModel):
    text: str
    territory_level: str
    territory_name: str
    author_id: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class ReportResponse(BaseModel):
    id: str
    text: str
    territory_level: str
    territory_name: str
    author_id: str
    created_at: datetime
    ai_labels: list[str]
    label_feedback: dict[str, bool]
    likes_count: int

    model_config = {"from_attributes": True}
