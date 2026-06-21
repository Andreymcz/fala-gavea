from __future__ import annotations

from pydantic import BaseModel


class KeywordItem(BaseModel):
    cluster_id: int
    terms: list[str]
    count: int


class KeywordListResponse(BaseModel):
    keywords: list[KeywordItem]
    total_reports: int
