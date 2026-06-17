from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class TerritoryLevel(str, Enum):
    NEIGHBORHOOD = "neighborhood"
    DISTRICT = "district"
    CITY = "city"


@dataclass
class Report:
    id: str
    text: str
    territory_level: TerritoryLevel
    territory_name: str
    author_id: str
    created_at: datetime
    # AI-enrichment extension points (populated by pipeline, not by human input)
    ai_labels: list[str] = field(default_factory=list)
    label_feedback: dict[str, bool] = field(default_factory=dict)
    likes_count: int = 0

    @staticmethod
    def create(
        text: str,
        territory_level: TerritoryLevel,
        territory_name: str,
        author_id: str,
    ) -> Report:
        return Report(
            id=str(uuid.uuid4()),
            text=text,
            territory_level=territory_level,
            territory_name=territory_name,
            author_id=author_id,
            created_at=datetime.now(UTC),
        )
