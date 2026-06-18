from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus


@dataclass
class ReportFilters:
    report_type_id: str | None = None
    urgency: Urgency | None = None
    status: ReportStatus | None = None
    since: datetime | None = None
    until: datetime | None = None
    bbox: tuple[float, float, float, float] | None = None  # (minLat, minLon, maxLat, maxLon)


class IReportRepository(ABC):
    @abstractmethod
    def save(self, report: Report) -> Report: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Report | None: ...

    @abstractmethod
    def find_all(self, filters: ReportFilters) -> list[Report]: ...
