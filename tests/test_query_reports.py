from __future__ import annotations

from datetime import UTC, datetime

import pytest

from fala_gavea.application.use_cases.reports.query_reports import QueryReports, QueryPage
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.repositories.report_repository import IReportRepository, ReportFilters
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

def _make_report(id: str) -> Report:
    return Report(
        id=id,
        text=f"Report {id}",
        lat=-22.9,
        lon=-43.2,
        urgency=Urgency.media,
        photo_url=None,
        report_type_id="rt-1",
        author_id="user-1",
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )


class FakeReportRepo(IReportRepository):
    def __init__(self, reports: list[Report]) -> None:
        self._reports = reports

    def save(self, report: Report) -> Report:
        return report

    def find_by_id(self, id: str) -> Report | None:
        return next((r for r in self._reports if r.id == id), None)

    def find_all(self, filters: ReportFilters) -> list[Report]:
        return list(self._reports)

    def find_page(
        self,
        filters: ReportFilters,
        *,
        limit: int,
        offset: int,
        order: str = "recent",
        candidate_cap: int = 500,
    ) -> tuple[list[Report], int]:
        items = list(self._reports[:candidate_cap])
        total = len(items)
        if order == "recent":
            return items[offset : offset + limit], total
        # order="none" — return all up to limit/candidate_cap
        return items[:limit], total


class FakeSearchPort(ISemanticSearchPort):
    def __init__(self, scores: dict[str, float]) -> None:
        self._scores = scores

    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]:
        return []

    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]:
        return []

    def rank(self, query: str, ids: list[str]) -> dict[str, float]:
        return {id_: self._scores[id_] for id_ in ids if id_ in self._scores}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_semantic_path_orders_by_score() -> None:
    """Items are returned in descending score order when q is provided."""
    r1 = _make_report("r1")
    r2 = _make_report("r2")
    r3 = _make_report("r3")
    repo = FakeReportRepo([r1, r2, r3])
    search = FakeSearchPort({"r1": 0.5, "r2": 0.9, "r3": 0.3})
    uc = QueryReports(repo, search)

    page = uc.execute(ReportFilters(), q="crime", limit=10, offset=0, max_results=100)

    assert page.ranked_by == "similarity"
    ids = [r.id for r, _ in page.items]
    assert ids == ["r2", "r1", "r3"]
    scores = [s for _, s in page.items]
    assert scores == [0.9, 0.5, 0.3]


def test_semantic_path_pagination() -> None:
    """Offset and limit slice the ranked list; total equals full filtered count."""
    reports = [_make_report(f"r{i}") for i in range(5)]
    scores = {f"r{i}": float(i) / 10 for i in range(5)}  # r4 highest
    repo = FakeReportRepo(reports)
    search = FakeSearchPort(scores)
    uc = QueryReports(repo, search)

    page = uc.execute(ReportFilters(), q="test", limit=2, offset=1, max_results=100)

    assert page.total == 5
    assert page.limit == 2
    assert page.offset == 1
    assert len(page.items) == 2
    # full sorted order: r4, r3, r2, r1, r0 — offset=1 → r3, r2
    assert page.items[0][0].id == "r3"
    assert page.items[1][0].id == "r2"


def test_recency_path_when_no_q() -> None:
    """Without q, recency order is used and scores are None."""
    r1 = _make_report("r1")
    r2 = _make_report("r2")
    repo = FakeReportRepo([r1, r2])
    search = FakeSearchPort({"r1": 0.9, "r2": 0.1})
    uc = QueryReports(repo, search)

    page = uc.execute(ReportFilters(), q=None, limit=10, offset=0, max_results=100)

    assert page.ranked_by == "recency"
    assert all(score is None for _, score in page.items)


def test_no_search_port_falls_back_to_recency() -> None:
    """When search_port is None, recency path is used even if q is set."""
    r1 = _make_report("r1")
    repo = FakeReportRepo([r1])
    uc = QueryReports(repo, None)

    page = uc.execute(ReportFilters(), q="anything", limit=10, offset=0, max_results=100)

    assert page.ranked_by == "recency"


def test_max_results_caps_candidate_set() -> None:
    """max_results limits the candidate pool in the semantic path."""
    reports = [_make_report(f"r{i}") for i in range(10)]
    # Only r0..r4 are in the repo view when candidate_cap=5
    # FakeReportRepo slices to candidate_cap via find_page with limit=max_results
    scores = {f"r{i}": float(i) for i in range(10)}
    repo = FakeReportRepo(reports)
    search = FakeSearchPort(scores)
    uc = QueryReports(repo, search)

    page = uc.execute(ReportFilters(), q="test", limit=10, offset=0, max_results=5)

    # candidate set is capped at 5
    assert page.total == 5
    assert len(page.items) == 5
