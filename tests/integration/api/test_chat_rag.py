from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

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

from fala_gavea.infrastructure.database.models import Base  # noqa: E402
from fala_gavea.infrastructure.database.session import SessionLocal  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository  # noqa: E402
from fala_gavea.presentation.api.dependencies import (  # noqa: E402
    get_db,
    get_llm_client,
    get_semantic_search_port,
)
from fala_gavea.presentation.api.main import create_app  # noqa: E402
from fala_gavea.domain.entities.user import User, UserRole  # noqa: E402
from fala_gavea.infrastructure.auth.password_service import PasswordService  # noqa: E402


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


def _stub_llm(response: str = "Resposta do LLM"):
    llm = MagicMock()
    llm.complete.return_value = response
    return llm


def _stub_search(hits=None):
    search = MagicMock()
    search.search.return_value = hits if hits is not None else []
    return search


@pytest.fixture
def app_with_stubs(db_session):
    """App with stub LLM and stub search injected, db overridden."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _stub_llm()
    app.dependency_overrides[get_semantic_search_port] = lambda: _stub_search()
    yield app
    app.dependency_overrides.clear()


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


def _token_headers(client: TestClient, email: str, password: str = "pass1234") -> dict:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# 1. Agent role → 200
# ---------------------------------------------------------------------------

def test_agent_gets_200(app_with_stubs, db_session):
    _create_user(db_session, UserRole.agent, "agent@chat.test")
    with TestClient(app_with_stubs) as client:
        headers = _token_headers(client, "agent@chat.test")
        resp = client.post("/nl/chat", json={"message": "buracos na rua"}, headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert "response" in body
    assert "cited_report_ids" in body
    assert isinstance(body["cited_report_ids"], list)


# ---------------------------------------------------------------------------
# 2. Citizen role → 403
# ---------------------------------------------------------------------------

def test_citizen_gets_403(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _stub_llm()
    app.dependency_overrides[get_semantic_search_port] = lambda: _stub_search()

    _create_user(db_session, UserRole.citizen, "citizen@chat.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@chat.test")
        resp = client.post("/nl/chat", json={"message": "calçada"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 3. Unauthenticated → 401
# ---------------------------------------------------------------------------

def test_unauthenticated_gets_401():
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/nl/chat", json={"message": "teste"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. LLM unavailable → 503
# ---------------------------------------------------------------------------

def test_llm_unavailable_gets_503(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: None  # unavailable
    app.dependency_overrides[get_semantic_search_port] = lambda: _stub_search()

    _create_user(db_session, UserRole.agent, "agent2@chat.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "agent2@chat.test")
        resp = client.post("/nl/chat", json={"message": "teste"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 503
    assert "LLM" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 5. Semantic search unavailable → 503
# ---------------------------------------------------------------------------

def test_search_unavailable_gets_503(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _stub_llm()
    app.dependency_overrides[get_semantic_search_port] = lambda: None  # unavailable

    _create_user(db_session, UserRole.agent, "agent3@chat.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "agent3@chat.test")
        resp = client.post("/nl/chat", json={"message": "teste"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 503
    assert "emantic" in resp.json()["detail"]
