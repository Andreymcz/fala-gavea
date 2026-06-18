from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ReportSummary(BaseModel):
    id: str
    text: str
    urgency: str
    status: str
    report_type_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForwardingCreate(BaseModel):
    institution: str
    proposed_solution: str
    report_ids: list[str]

    @field_validator("institution")
    @classmethod
    def institution_length(cls, v: str) -> str:
        v = v.strip()
        if not (3 <= len(v) <= 200):
            raise ValueError("institution must be 3-200 characters")
        return v

    @field_validator("proposed_solution")
    @classmethod
    def solution_length(cls, v: str) -> str:
        v = v.strip()
        if not (20 <= len(v) <= 5000):
            raise ValueError("proposed_solution must be 20-5000 characters")
        return v

    @field_validator("report_ids")
    @classmethod
    def report_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("report_ids must contain at least one report id")
        return v


class ForwardingUpdate(BaseModel):
    institution: str | None = None
    proposed_solution: str | None = None

    @field_validator("institution")
    @classmethod
    def institution_length(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not (3 <= len(v) <= 200):
            raise ValueError("institution must be 3-200 characters")
        return v

    @field_validator("proposed_solution")
    @classmethod
    def solution_length(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not (20 <= len(v) <= 5000):
            raise ValueError("proposed_solution must be 20-5000 characters")
        return v


class ForwardingStatusUpdate(BaseModel):
    status: str


class ForwardingResponse(BaseModel):
    id: str
    institution: str
    proposed_solution: str
    status: str
    agent_id: str
    reports: list[ReportSummary]
    created_at: datetime
    updated_at: datetime
