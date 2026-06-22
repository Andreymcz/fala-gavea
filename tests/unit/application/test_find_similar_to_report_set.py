from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from fala_gavea.application.use_cases.reports.find_similar_to_report_set import (
    FindSimilarToReportSet,
)
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency


def _make_report(report_id: str, status: ReportStatus = ReportStatus.pendente) -> Report:
    return Report(
        id=report_id,
        text=f"Relato {report_id}",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        status=status,
        report_type_id="rt-1",
        author_id="user-1",
        photo_url=None,
        created_at=datetime.now(timezone.utc),
    )


def test_returns_pendente_neighbors():
    search_port = MagicMock()
    search_port.similar_to_set.return_value = [("n1", 0.9)]
    reports = {"n1": _make_report("n1")}
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = FindSimilarToReportSet(report_repo, search_port).execute(["seed"], 5)

    assert [(r.id, s) for r, s in results] == [("n1", 0.9)]
    search_port.similar_to_set.assert_called_once_with(["seed"], 5)


def test_filters_non_pendente():
    search_port = MagicMock()
    search_port.similar_to_set.return_value = [("open", 0.8), ("closed", 0.7)]
    reports = {
        "open": _make_report("open", ReportStatus.pendente),
        "closed": _make_report("closed", ReportStatus.encaminhado),
    }
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = FindSimilarToReportSet(report_repo, search_port).execute(["seed"], 5)

    assert [r.id for r, _ in results] == ["open"]


def test_excludes_seed_ids():
    search_port = MagicMock()
    search_port.similar_to_set.return_value = [("seed", 1.0), ("n1", 0.5)]
    reports = {"seed": _make_report("seed"), "n1": _make_report("n1")}
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = FindSimilarToReportSet(report_repo, search_port).execute(["seed"], 5)

    assert [r.id for r, _ in results] == ["n1"]


def test_skips_missing_neighbor_ids():
    search_port = MagicMock()
    search_port.similar_to_set.return_value = [("n1", 0.5), ("ghost", 0.4)]
    reports = {"n1": _make_report("n1")}
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = FindSimilarToReportSet(report_repo, search_port).execute(["seed"], 5)

    assert [r.id for r, _ in results] == ["n1"]
