from __future__ import annotations

from fala_gavea.domain.entities.report import Report, ReportStatus
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


class FindSimilarToReportSet:
    """Centroid-based neighbors of a set of reports (Rec 5 / D-010). Queries the
    search port for the centroid of report_ids, hydrates each hit from SQLite,
    excludes the seed ids, and keeps only reports whose status is `pendente`
    (D-010: 'relato aberto' = pendente only). Ids without a matching Report are
    skipped."""

    def __init__(self, report_repo: IReportRepository, search_port: ISemanticSearchPort) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(self, report_ids: list[str], n: int = 5) -> list[tuple[Report, float]]:
        seed = set(report_ids)
        hits = self._search_port.similar_to_set(report_ids, n)
        results: list[tuple[Report, float]] = []
        for rid, score in hits:
            if rid in seed:
                continue
            report = self._report_repo.find_by_id(rid)
            if report is None:
                continue
            if report.status != ReportStatus.pendente:
                continue
            results.append((report, score))
        return results
