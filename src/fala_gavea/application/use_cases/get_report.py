from __future__ import annotations

from ...domain.entities.report import Report
from ...domain.exceptions import ReportNotFoundError
from ...domain.repositories.report_repository import ReportRepository


class GetReport:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    def execute(self, id: str) -> Report:
        entity = self._repo.find_by_id(id)
        if entity is None:
            raise ReportNotFoundError(id)
        return entity
