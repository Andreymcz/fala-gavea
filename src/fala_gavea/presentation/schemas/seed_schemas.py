from __future__ import annotations

from pydantic import BaseModel


class SeedErrorItem(BaseModel):
    row: int
    reason: str


class SeedRelatosResponse(BaseModel):
    inserted: int
    skipped: int
    errors: list[SeedErrorItem]


class SeedTopicosResponse(BaseModel):
    inserted: int
    skipped: int
    errors: list[SeedErrorItem]


class WipedCounts(BaseModel):
    reports: int
    forwardings: int
    report_types: int


class WipeResponse(BaseModel):
    wiped: WipedCounts
