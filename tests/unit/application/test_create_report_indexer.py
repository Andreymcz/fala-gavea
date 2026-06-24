from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock


from fala_gavea.application.use_cases.reports.create_report import CreateReport
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency


def _make_report() -> Report:
    return Report(
        id="report-1",
        text="Buraco na rua principal da Gavea",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        status=ReportStatus.pendente,
        report_type_id="rt-1",
        author_id="user-1",
        photo_url=None,
        created_at=datetime.now(timezone.utc),
    )


def _make_use_case(indexer=None):
    report = _make_report()
    report_repo = MagicMock()
    report_repo.save.return_value = report

    report_type = MagicMock()
    report_type.active = True
    report_type_repo = MagicMock()
    report_type_repo.find_by_id.return_value = report_type

    return CreateReport(report_repo, report_type_repo, indexer=indexer), report


def _execute(use_case):
    return use_case.execute(
        text="Buraco na rua principal da Gavea",
        lat=-22.97,
        lon=-43.22,
        urgency="alta",
        report_type_id="rt-1",
        author_id="user-1",
    )


def test_indexer_called_after_save():
    mock_indexer = MagicMock()
    use_case, report = _make_use_case(indexer=mock_indexer)
    result, _ = _execute(use_case)
    mock_indexer.index.assert_called_once_with(report)
    assert result is report


def test_indexer_failure_does_not_raise():
    mock_indexer = MagicMock()
    mock_indexer.index.side_effect = Exception("chroma down")
    use_case, report = _make_use_case(indexer=mock_indexer)
    result, _ = _execute(use_case)
    assert result is report


def test_no_indexer_skips_index():
    use_case, report = _make_use_case(indexer=None)
    result, _ = _execute(use_case)
    assert result is report
