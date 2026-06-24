from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fala_gavea.application.use_cases.votes.cast_vote import CastVoteUseCase
from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.exceptions import InvalidInputError, SelfVoteError


def _make_report(author_id: str) -> Report:
    return Report(
        id=str(uuid.uuid4()),
        text="Test report text",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.media,
        photo_url=None,
        report_type_id=str(uuid.uuid4()),
        author_id=author_id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )


def _make_forwarding(agent_id: str) -> Forwarding:
    return Forwarding(
        id=str(uuid.uuid4()),
        institution="SEOP",
        proposed_solution="Fix the lighting",
        status=ForwardingStatus.aguardando_solucao,
        agent_id=agent_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_use_case(report=None, forwarding=None):
    vote_repo = MagicMock()
    vote_repo.cast.side_effect = lambda v: v
    report_repo = MagicMock()
    report_repo.find_by_id.return_value = report
    forwarding_repo = MagicMock()
    forwarding_repo.find_by_id.return_value = forwarding
    return CastVoteUseCase(vote_repo, report_repo, forwarding_repo)


def test_valid_upvote_on_report():
    author_id = str(uuid.uuid4())
    voter_id = str(uuid.uuid4())
    report = _make_report(author_id)
    uc = _make_use_case(report=report)
    result = uc.execute(voter_id, "report", report.id, 1)
    assert result.value == 1
    assert result.voter_id == voter_id


def test_self_vote_raises_error():
    author_id = str(uuid.uuid4())
    report = _make_report(author_id)
    uc = _make_use_case(report=report)
    with pytest.raises(SelfVoteError):
        uc.execute(author_id, "report", report.id, 1)


def test_invalid_target_type():
    uc = _make_use_case()
    with pytest.raises(InvalidInputError):
        uc.execute(str(uuid.uuid4()), "comment", str(uuid.uuid4()), 1)


def test_invalid_value():
    author_id = str(uuid.uuid4())
    voter_id = str(uuid.uuid4())
    report = _make_report(author_id)
    uc = _make_use_case(report=report)
    with pytest.raises(InvalidInputError):
        uc.execute(voter_id, "report", report.id, 0)


def test_valid_downvote_on_forwarding():
    agent_id = str(uuid.uuid4())
    voter_id = str(uuid.uuid4())
    forwarding = _make_forwarding(agent_id)
    uc = _make_use_case(forwarding=forwarding)
    result = uc.execute(voter_id, "forwarding", forwarding.id, -1)
    assert result.value == -1
