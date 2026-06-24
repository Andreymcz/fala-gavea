from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus


@dataclass
class ReportFilters:
    report_type_ids: list[str] | None = None
    urgencies: list[Urgency] | None = None
    statuses: list[ReportStatus] | None = None
    since: datetime | None = None
    until: datetime | None = None
    bbox: tuple[float, float, float, float] | None = None  # (minLat, minLon, maxLat, maxLon)
    text: str | None = None
    author_id: str | None = None


class IReportRepository(ABC):
    @abstractmethod
    def save(self, report: Report) -> Report: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Report | None: ...

    @abstractmethod
    def find_all(self, filters: ReportFilters) -> list[Report]: ...

    @abstractmethod
    def find_by_ids(self, ids: list[str]) -> list[Report]: ...

    @abstractmethod
    def find_page(
        self,
        filters: ReportFilters,
        *,
        limit: int,
        offset: int,
        order: str = "recent",
        candidate_cap: int = 500,
    ) -> tuple[list[Report], int]: ...
