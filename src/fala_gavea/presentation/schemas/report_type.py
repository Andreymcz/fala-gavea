from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class ReportTypeCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        v = v.strip()
        if not (3 <= len(v) <= 100):
            raise ValueError("name must be 3-100 characters")
        return v


class ReportTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ReportTypeResponse(BaseModel):
    id: str
    name: str
    description: str | None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
