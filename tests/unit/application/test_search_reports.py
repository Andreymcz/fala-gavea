from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from fala_gavea.application.use_cases.reports.search_reports import SearchReports
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency


def _make_report(report_id: str) -> Report:
    return Report(
        id=report_id,
        text=f"Relato {report_id}",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        status=ReportStatus.pendente,
        report_type_id="rt-1",
        author_id="user-1",
        photo_url=None,
        created_at=datetime.now(timezone.utc),
    )


def test_search_hydrates_and_keeps_score():
    search_port = MagicMock()
    search_port.search.return_value = [("r1", 0.9), ("r2", 0.7)]

    reports = {"r1": _make_report("r1"), "r2": _make_report("r2")}
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = SearchReports(report_repo, search_port).execute("buraco", 10)

    assert [(r.id, score) for r, score in results] == [("r1", 0.9), ("r2", 0.7)]
    assert all(isinstance(r, Report) for r, _ in results)


def test_search_skips_missing_ids():
    search_port = MagicMock()
    search_port.search.return_value = [("r1", 0.9), ("ghost", 0.5)]

    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: _make_report("r1") if rid == "r1" else None

    results = SearchReports(report_repo, search_port).execute("buraco", 10)

    assert [r.id for r, _ in results] == ["r1"]


def test_search_passes_n():
    search_port = MagicMock()
    search_port.search.return_value = []
    report_repo = MagicMock()

    SearchReports(report_repo, search_port).execute("buraco", 3)

    search_port.search.assert_called_once_with("buraco", 3)
