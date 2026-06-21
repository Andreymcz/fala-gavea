from __future__ import annotations

from dataclasses import dataclass

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.report_repository import IReportRepository, ReportFilters
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


@dataclass
class QueryPage:
    items: list[tuple[Report, float | None]]
    total: int
    limit: int
    offset: int
    ranked_by: str  # "similarity" or "recency"


class QueryReports:
    def __init__(
        self,
        report_repo: IReportRepository,
        search_port: ISemanticSearchPort | None,
    ) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(
        self,
        filters: ReportFilters,
        *,
        q: str | None,
        limit: int,
        offset: int,
        max_results: int,
    ) -> QueryPage:
        if q and self._search_port is not None:
            # Semantic path: filter SQL -> rank in memory -> paginate over ranked set
            rows, _ = self._report_repo.find_page(
                filters,
                limit=max_results,
                offset=0,
                order="none",
                candidate_cap=max_results,
            )
            scores = self._search_port.rank(q, [r.id for r in rows])
            # sort descending by score (missing scores sort last)
            rows.sort(key=lambda r: scores.get(r.id, -1.0), reverse=True)
            total = len(rows)
            page = rows[offset : offset + limit]
            items = [(r, scores.get(r.id)) for r in page]
            return QueryPage(items=items, total=total, limit=limit, offset=offset, ranked_by="similarity")
        else:
            # Recency path
            rows, total = self._report_repo.find_page(
                filters,
                limit=limit,
                offset=offset,
                order="recent",
                candidate_cap=max_results,
            )
            items = [(r, None) for r in rows]
            return QueryPage(items=items, total=total, limit=limit, offset=offset, ranked_by="recency")
