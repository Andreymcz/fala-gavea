from __future__ import annotations

import uuid
from datetime import UTC, datetime
from hashlib import sha256
from unittest.mock import MagicMock

from fala_gavea.application.use_cases.reports.create_report import CreateReport
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.entities.report_type import ReportType


def _make_report_type(rt_id: str) -> ReportType:
    return ReportType(
        id=rt_id,
        name="Test Type",
        description=None,
        active=True,
        created_at=datetime.now(UTC),
    )


def _make_mock_repos(rt_id: str):
    report_type_repo = MagicMock()
    report_type_repo.find_by_id.return_value = _make_report_type(rt_id)

    report_repo = MagicMock()

    def save_side_effect(report: Report) -> Report:
        return report

    report_repo.save.side_effect = save_side_effect
    return report_repo, report_type_repo


def test_anonymous_report_returns_token_and_null_author():
    rt_id = str(uuid.uuid4())
    report_repo, report_type_repo = _make_mock_repos(rt_id)
    anon_token_repo = MagicMock()
    anon_token_repo.save.side_effect = lambda t: t

    uc = CreateReport(report_repo, report_type_repo, anon_token_repo=anon_token_repo)
    report, token = uc.execute(
        text="Poste apagado na rua principal",
        lat=-22.971,
        lon=-43.211,
        urgency="media",
        report_type_id=rt_id,
        author_id=None,
        anonymous=True,
    )

    assert report.author_id is None
    assert token is not None
    assert len(token) > 0
    # Verify token was saved with correct hash
    assert anon_token_repo.save.called
    saved_token = anon_token_repo.save.call_args[0][0]
    assert saved_token.token_hash == sha256(token.encode()).hexdigest()
    assert saved_token.report_id == report.id


def test_authenticated_report_returns_null_token():
    rt_id = str(uuid.uuid4())
    report_repo, report_type_repo = _make_mock_repos(rt_id)
    anon_token_repo = MagicMock()

    uc = CreateReport(report_repo, report_type_repo, anon_token_repo=anon_token_repo)
    author_id = str(uuid.uuid4())
    report, token = uc.execute(
        text="Poste apagado na rua principal",
        lat=-22.971,
        lon=-43.211,
        urgency="media",
        report_type_id=rt_id,
        author_id=author_id,
        anonymous=False,
    )

    assert report.author_id == author_id
    assert token is None
    anon_token_repo.save.assert_not_called()
