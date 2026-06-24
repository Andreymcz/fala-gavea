from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.entities.vote import Vote
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from fala_gavea.infrastructure.repositories.vote_repository import SQLAlchemyVoteRepository


def _create_user(db_session) -> str:
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@test.com",
        password_hash=ps.hash_password("pass1234"),
        name="Test User",
        role=UserRole.citizen,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(user)
    return user.id


def _vote(voter_id: str, target_type: str = "report", target_id: str | None = None, value: int = 1) -> Vote:
    return Vote(
        id=str(uuid.uuid4()),
        voter_id=voter_id,
        target_type=target_type,
        target_id=target_id or str(uuid.uuid4()),
        value=value,
        created_at=datetime.now(UTC),
    )


def test_cast_and_get_summary(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    target_id = str(uuid.uuid4())
    voter_id = _create_user(db_session)
    v = _vote(voter_id, "report", target_id, 1)
    repo.cast(v)
    summary = repo.get_summary("report", target_id, voter_id)
    assert summary.upvotes == 1
    assert summary.downvotes == 0
    assert summary.user_vote == 1


def test_cast_downvote(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    target_id = str(uuid.uuid4())
    voter_id = _create_user(db_session)
    repo.cast(_vote(voter_id, "report", target_id, -1))
    summary = repo.get_summary("report", target_id, voter_id)
    assert summary.downvotes == 1
    assert summary.upvotes == 0
    assert summary.user_vote == -1


def test_duplicate_vote_upserts(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    target_id = str(uuid.uuid4())
    voter_id = _create_user(db_session)
    repo.cast(_vote(voter_id, "report", target_id, 1))
    repo.cast(_vote(voter_id, "report", target_id, -1))  # change to downvote
    summary = repo.get_summary("report", target_id, voter_id)
    assert summary.upvotes == 0
    assert summary.downvotes == 1
    assert summary.user_vote == -1


def test_retract_removes_vote(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    target_id = str(uuid.uuid4())
    voter_id = _create_user(db_session)
    repo.cast(_vote(voter_id, "report", target_id, 1))
    repo.retract(voter_id, "report", target_id)
    summary = repo.get_summary("report", target_id, voter_id)
    assert summary.upvotes == 0
    assert summary.user_vote is None


def test_retract_noop_if_absent(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    # Should not raise
    repo.retract(str(uuid.uuid4()), "report", str(uuid.uuid4()))


def test_get_summary_no_voter_id(db_session):
    repo = SQLAlchemyVoteRepository(db_session)
    target_id = str(uuid.uuid4())
    voter_id = _create_user(db_session)
    repo.cast(_vote(voter_id, "report", target_id, 1))
    summary = repo.get_summary("report", target_id)
    assert summary.upvotes == 1
    assert summary.user_vote is None
