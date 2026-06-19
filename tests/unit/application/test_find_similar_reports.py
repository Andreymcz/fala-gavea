from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from fala_gavea.application.use_cases.reports.find_similar_reports import FindSimilarReports
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.exceptions import ReportNotFoundError


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


def test_similar_returns_neighbors():
    search_port = MagicMock()
    search_port.similar.return_value = [("r2", 0.8)]

    reports = {"base": _make_report("base"), "r2": _make_report("r2")}
    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = lambda rid: reports.get(rid)

    results = FindSimilarReports(report_repo, search_port).execute("base", 5)

    assert [(r.id, score) for r, score in results] == [("r2", 0.8)]
    search_port.similar.assert_called_once_with("base", 5)


def test_similar_base_not_found_raises():
    search_port = MagicMock()
    report_repo = MagicMock()
    report_repo.find_by_id.return_value = None

    with pytest.raises(ReportNotFoundError):
        FindSimilarReports(report_repo, search_port).execute("missing", 5)

    search_port.similar.assert_not_called()


def test_similar_skips_missing_neighbor_ids():
    search_port = MagicMock()
    search_port.similar.return_value = [("r2", 0.8), ("ghost", 0.4)]

    def _find(rid: str):
        if rid == "base":
            return _make_report("base")
        if rid == "r2":
            return _make_report("r2")
        return None

    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = _find

    results = FindSimilarReports(report_repo, search_port).execute("base", 5)

    assert [r.id for r, _ in results] == ["r2"]
