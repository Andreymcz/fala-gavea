from __future__ import annotations

from pydantic import BaseModel


class SeedErrorItem(BaseModel):
    row: int
    reason: str


class SeedRelatosResponse(BaseModel):
    inserted: int
    skipped: int
    errors: list[SeedErrorItem]
