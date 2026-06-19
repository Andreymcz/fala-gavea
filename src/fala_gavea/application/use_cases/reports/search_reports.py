from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


class SearchReports:
    """Semantic search over reports: queries the search port, hydrates each hit
    by id, and preserves the similarity score. Vectorstore ids without a
    matching Report in SQLite (e.g. deleted reports) are skipped."""

    def __init__(self, report_repo: IReportRepository, search_port: ISemanticSearchPort) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(self, query: str, n: int = 10) -> list[tuple[Report, float]]:
        hits = self._search_port.search(query, n)
        results: list[tuple[Report, float]] = []
        for report_id, score in hits:
            report = self._report_repo.find_by_id(report_id)
            if report is not None:  # vectorstore pode ter id sem Report no SQLite
                results.append((report, score))
        return results
