from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedFilterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    body: dict[str, Any]


class SavedFilterUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    body: dict[str, Any] | None = None


class SavedFilterResponse(BaseModel):
    id: str
    name: str
    body: dict[str, Any]
    schema_ver: str
    created_at: datetime
    updated_at: datetime
    deprecated_fields: list[str] = []
