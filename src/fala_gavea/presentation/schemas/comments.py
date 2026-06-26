from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CommentResponse(BaseModel):
    id: str
    forwarding_id: str
    # Omitted (null) for unauthenticated/public viewers so the public forwarding
    # view never exposes which user authored a comment. Populated only for
    # authenticated requests, where it is needed for self-delete and moderation.
    author_id: str | None = None
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AddCommentRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_length(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 500):
            raise ValueError("text must be 1-500 characters")
        return v
