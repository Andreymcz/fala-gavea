from __future__ import annotations

from ...domain.entities.report import Report
from ...domain.repositories.report_repository import ReportRepository


class ListReports:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    def execute(self, limit: int = 50, offset: int = 0) -> list[Report]:
        return self._repo.find_all(limit=limit, offset=offset)
