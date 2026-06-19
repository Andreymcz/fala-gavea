from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import ReportNotFoundError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


class FindSimilarReports:
    """Semantic neighbors of a base report. Validates the base report exists
    (else ReportNotFoundError -> 404), then hydrates each neighbor by id. The
    search port already excludes the base report from its results; ids without
    a matching Report in SQLite are skipped."""

    def __init__(self, report_repo: IReportRepository, search_port: ISemanticSearchPort) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(self, report_id: str, n: int = 5) -> list[tuple[Report, float]]:
        if self._report_repo.find_by_id(report_id) is None:
            raise ReportNotFoundError(f"Report not found: {report_id}")
        hits = self._search_port.similar(report_id, n)
        results: list[tuple[Report, float]] = []
        for rid, score in hits:
            report = self._report_repo.find_by_id(rid)
            if report is not None:
                results.append((report, score))
        return results
