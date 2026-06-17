from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import ReportNotFoundError
from fala_gavea.domain.repositories.report_repository import IReportRepository


class GetReport:
    def __init__(self, report_repo: IReportRepository) -> None:
        self._report_repo = report_repo

    def execute(self, id: str) -> Report:
        report = self._report_repo.find_by_id(id)
        if report is None:
            raise ReportNotFoundError(f"Report not found: {id}")
        return report
