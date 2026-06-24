from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import fala_gavea.infrastructure.database.session as _db_mod

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db_mod.engine = _TEST_ENGINE
_db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)

from fala_gavea.domain.entities.comment import Comment  # noqa: E402
from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus  # noqa: E402
from fala_gavea.domain.entities.user import User, UserRole  # noqa: E402
from fala_gavea.infrastructure.database.models import Base  # noqa: E402
from fala_gavea.infrastructure.database.session import SessionLocal  # noqa: E402
from fala_gavea.infrastructure.repositories.comment_repository import SQLAlchemyCommentRepository  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository  # noqa: E402
from fala_gavea.infrastructure.auth.password_service import PasswordService  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(_TEST_ENGINE)
    Base.metadata.create_all(_TEST_ENGINE)


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def _make_user(session, role: str = "citizen") -> User:
    ps = PasswordService()
    user = User(
        id=str(uuid4()),
        email=f"{uuid4()}@test.com",
        password_hash=ps.hash_password("password123"),
        name="Test User",
        role=UserRole(role),
        created_at=datetime.now(UTC),
    )
    repo = SQLAlchemyUserRepository(session)
    repo.save(user)
    return user


def _make_forwarding(session, agent_id: str) -> Forwarding:
    fwd = Forwarding(
        id=str(uuid4()),
        institution="Comlurb",
        proposed_solution="Clean the street",
        status=ForwardingStatus.aguardando_solucao,
        agent_id=agent_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    SQLAlchemyForwardingRepository(session).save(fwd)
    return fwd


def test_add_and_find_by_id(session):
    agent = _make_user(session, "agent")
    fwd = _make_forwarding(session, agent.id)
    author = _make_user(session, "citizen")

    repo = SQLAlchemyCommentRepository(session)
    comment = Comment(
        id=str(uuid4()),
        forwarding_id=fwd.id,
        author_id=author.id,
        text="Ótimo trabalho!",
        created_at=datetime.now(UTC),
    )
    saved = repo.add(comment)

    assert saved.id == comment.id
    found = repo.find_by_id(comment.id)
    assert found is not None
    assert found.text == "Ótimo trabalho!"


def test_delete_removes_comment(session):
    agent = _make_user(session, "agent")
    fwd = _make_forwarding(session, agent.id)
    author = _make_user(session, "citizen")

    repo = SQLAlchemyCommentRepository(session)
    comment = Comment(
        id=str(uuid4()),
        forwarding_id=fwd.id,
        author_id=author.id,
        text="Comentário a apagar",
        created_at=datetime.now(UTC),
    )
    repo.add(comment)
    repo.delete(comment.id)
    assert repo.find_by_id(comment.id) is None


def test_delete_noop_if_absent(session):
    repo = SQLAlchemyCommentRepository(session)
    # Should not raise
    repo.delete("nonexistent-id")


def test_list_by_forwarding_ordered(session):
    agent = _make_user(session, "agent")
    fwd = _make_forwarding(session, agent.id)
    author = _make_user(session, "citizen")

    repo = SQLAlchemyCommentRepository(session)
    t1 = datetime(2024, 1, 1, 10, 0, 0)
    t2 = datetime(2024, 1, 1, 11, 0, 0)
    c1 = Comment(id=str(uuid4()), forwarding_id=fwd.id, author_id=author.id, text="First", created_at=t1)
    c2 = Comment(id=str(uuid4()), forwarding_id=fwd.id, author_id=author.id, text="Second", created_at=t2)
    repo.add(c2)
    repo.add(c1)

    comments = repo.list_by_forwarding(fwd.id)
    assert [c.text for c in comments] == ["First", "Second"]


def test_list_by_forwarding_returns_empty_for_unknown(session):
    repo = SQLAlchemyCommentRepository(session)
    assert repo.list_by_forwarding("ghost-id") == []
