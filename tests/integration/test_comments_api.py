from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
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

from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus  # noqa: E402
from fala_gavea.domain.entities.user import User, UserRole  # noqa: E402
from fala_gavea.infrastructure.auth.password_service import PasswordService  # noqa: E402
from fala_gavea.infrastructure.database.models import Base  # noqa: E402
from fala_gavea.infrastructure.database.session import SessionLocal  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository  # noqa: E402
from fala_gavea.presentation.api.dependencies import get_db  # noqa: E402
from fala_gavea.presentation.api.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(_TEST_ENGINE)
    Base.metadata.create_all(_TEST_ENGINE)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def app(db_session):
    _app = create_app()
    _app.dependency_overrides[get_db] = lambda: db_session
    yield _app
    _app.dependency_overrides.clear()


def _create_user(db_session, role: UserRole, email: str, password: str = "pass1234") -> User:
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=ps.hash_password(password),
        name=f"User {role.value}",
        role=role,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(user)
    return user


def _create_forwarding(db_session, agent_id: str) -> Forwarding:
    fwd = Forwarding(
        id=str(uuid.uuid4()),
        institution="Comlurb",
        proposed_solution="Limpar a rua",
        status=ForwardingStatus.aguardando_solucao,
        agent_id=agent_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    SQLAlchemyForwardingRepository(db_session).save(fwd)
    return fwd


def _token_headers(client: TestClient, email: str, password: str = "pass1234") -> dict:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# GET /forwardings/{forwarding_id}/comments — public, no auth required
# ---------------------------------------------------------------------------

def test_list_comments_public_empty(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        resp = client.get(f"/forwardings/{fwd.id}/comments")

    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /forwardings/{forwarding_id}/comments — any authenticated user
# ---------------------------------------------------------------------------

def test_add_comment_citizen(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c2.test")
    citizen = _create_user(db_session, UserRole.citizen, "citizen@c2.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@c2.test")
        resp = client.post(
            f"/forwardings/{fwd.id}/comments",
            json={"text": "Bom encaminhamento!"},
            headers=headers,
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["text"] == "Bom encaminhamento!"
    assert body["forwarding_id"] == fwd.id
    assert body["author_id"] == citizen.id


def test_add_comment_returns_404_for_unknown_forwarding(app, db_session):
    _create_user(db_session, UserRole.citizen, "citizen@c3.test")

    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@c3.test")
        resp = client.post(
            "/forwardings/ghost-fwd/comments",
            json={"text": "Comentário"},
            headers=headers,
        )

    assert resp.status_code == 404


def test_add_comment_unauthenticated_returns_401(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c4.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        resp = client.post(
            f"/forwardings/{fwd.id}/comments",
            json={"text": "Comentário"},
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /forwardings/{forwarding_id}/comments/{comment_id}
# ---------------------------------------------------------------------------

def test_delete_comment_by_owner(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c5.test")
    _create_user(db_session, UserRole.citizen, "citizen@c5.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@c5.test")
        post_resp = client.post(
            f"/forwardings/{fwd.id}/comments",
            json={"text": "A apagar"},
            headers=headers,
        )
        assert post_resp.status_code == 201
        comment_id = post_resp.json()["id"]

        del_resp = client.delete(
            f"/forwardings/{fwd.id}/comments/{comment_id}",
            headers=headers,
        )

    assert del_resp.status_code == 204


def test_delete_comment_by_agent(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c6.test")
    _create_user(db_session, UserRole.citizen, "citizen@c6.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        citizen_headers = _token_headers(client, "citizen@c6.test")
        post_resp = client.post(
            f"/forwardings/{fwd.id}/comments",
            json={"text": "Comentário do cidadão"},
            headers=citizen_headers,
        )
        comment_id = post_resp.json()["id"]

        agent_headers = _token_headers(client, "agent@c6.test")
        del_resp = client.delete(
            f"/forwardings/{fwd.id}/comments/{comment_id}",
            headers=agent_headers,
        )

    assert del_resp.status_code == 204


def test_delete_comment_forbidden_for_other_citizen(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c7.test")
    _create_user(db_session, UserRole.citizen, "citizen1@c7.test")
    _create_user(db_session, UserRole.citizen, "citizen2@c7.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        h1 = _token_headers(client, "citizen1@c7.test")
        post_resp = client.post(
            f"/forwardings/{fwd.id}/comments",
            json={"text": "Comentário do cidadão 1"},
            headers=h1,
        )
        comment_id = post_resp.json()["id"]

        h2 = _token_headers(client, "citizen2@c7.test")
        del_resp = client.delete(
            f"/forwardings/{fwd.id}/comments/{comment_id}",
            headers=h2,
        )

    assert del_resp.status_code == 403


def test_delete_comment_not_found(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c8.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        headers = _token_headers(client, "agent@c8.test")
        resp = client.delete(
            f"/forwardings/{fwd.id}/comments/ghost-comment",
            headers=headers,
        )

    assert resp.status_code == 404


def test_list_comments_after_post(app, db_session):
    agent = _create_user(db_session, UserRole.agent, "agent@c9.test")
    _create_user(db_session, UserRole.citizen, "citizen@c9.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@c9.test")
        client.post(f"/forwardings/{fwd.id}/comments", json={"text": "Comentário 1"}, headers=headers)
        client.post(f"/forwardings/{fwd.id}/comments", json={"text": "Comentário 2"}, headers=headers)

        resp = client.get(f"/forwardings/{fwd.id}/comments")

    assert resp.status_code == 200
    texts = [c["text"] for c in resp.json()]
    assert "Comentário 1" in texts
    assert "Comentário 2" in texts


def test_list_comments_public_hides_author_id(app, db_session):
    """Unauthenticated/public GET must NOT expose author_id (privacy)."""
    agent = _create_user(db_session, UserRole.agent, "agent@c10.test")
    citizen = _create_user(db_session, UserRole.citizen, "citizen@c10.test")
    fwd = _create_forwarding(db_session, agent.id)

    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@c10.test")
        client.post(f"/forwardings/{fwd.id}/comments", json={"text": "Olá"}, headers=headers)

        # Public (no Authorization header) — author_id must be null.
        public_resp = client.get(f"/forwardings/{fwd.id}/comments")
        # Authenticated — author_id must be present.
        authed_resp = client.get(f"/forwardings/{fwd.id}/comments", headers=headers)

    assert public_resp.status_code == 200
    assert public_resp.json()[0]["author_id"] is None

    assert authed_resp.status_code == 200
    assert authed_resp.json()[0]["author_id"] == citizen.id
