from __future__ import annotations
from pydantic import BaseModel, field_validator


class NLFilterRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        if len(v) > 500:
            raise ValueError("text must be 500 characters or fewer")
        return v


class NLFilterResponse(BaseModel):
    body: dict
    warnings: list[str] = []
