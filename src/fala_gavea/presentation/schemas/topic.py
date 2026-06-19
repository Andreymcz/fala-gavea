from __future__ import annotations

from pydantic import BaseModel


class TopicItem(BaseModel):
    topic_id: int
    terms: list[str]
    count: int


class TopicListResponse(BaseModel):
    topics: list[TopicItem]
    total_reports: int  # total docs passed to model
