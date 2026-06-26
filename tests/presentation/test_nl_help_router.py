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

from fala_gavea.domain.entities.user import User, UserRole  # noqa: E402
from fala_gavea.domain.repositories.doc_ports import DocChunk, DocSearchHit, IDocSearchPort  # noqa: E402
from fala_gavea.domain.repositories.semantic_ports import ILLMClient  # noqa: E402
from fala_gavea.infrastructure.auth.password_service import PasswordService  # noqa: E402
from fala_gavea.infrastructure.database.models import Base  # noqa: E402
from fala_gavea.infrastructure.database.session import SessionLocal  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import (  # noqa: E402
    SQLAlchemyUserRepository,
)
from fala_gavea.presentation.api.dependencies import (  # noqa: E402
    get_db,
    get_doc_search_port,
    get_llm_client,
)
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


class _RecordingSearchPort(IDocSearchPort):
    """Fake search port that records the roles passed to .search and returns one hit."""

    def __init__(self) -> None:
        self.received_roles: list[str] | None = None

    def search(self, query: str, *, roles: list[str], n: int = 5) -> list[DocSearchHit]:
        self.received_roles = roles
        chunk = DocChunk(
            chunk_id="docs/guide.md#0",
            text="A plataforma Fala-Gávea permite registrar relatos.",
            source_path="docs/guide.md",
            doc_type="guide",
            section_title="Introdução",
            chunk_index=0,
            role_visibility="public",
        )
        return [DocSearchHit(chunk=chunk, score=0.9)]

    def ready(self) -> bool:
        return True


class _StubLLM(ILLMClient):
    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        return "Resposta de ajuda do assistente."


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
# (a) Unauthenticated → 401
# ---------------------------------------------------------------------------

def test_unauthenticated_gets_401():
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/nl/help", json={"message": "como funciona?"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# (b) Citizen → roles=["public"]
# ---------------------------------------------------------------------------

def test_citizen_uses_public_only(db_session):
    app = create_app()
    search = _RecordingSearchPort()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _StubLLM()
    app.dependency_overrides[get_doc_search_port] = lambda: search

    _create_user(db_session, UserRole.citizen, "citizen@help.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "citizen@help.test")
        resp = client.post("/nl/help", json={"message": "como funciona?"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["response"] == "Resposta de ajuda do assistente."
    assert isinstance(body["cited_docs"], list)
    assert body["cited_docs"][0]["source_path"] == "docs/guide.md"
    assert body["cited_docs"][0]["section_title"] == "Introdução"
    assert body["cited_docs"][0]["score"] == 0.9
    assert body["cited_docs"][0]["doc_type"] == "guide"
    assert search.received_roles == ["public"]


# ---------------------------------------------------------------------------
# (c) Admin → roles=["public", "internal"]
# ---------------------------------------------------------------------------

def test_admin_uses_public_and_internal(db_session):
    app = create_app()
    search = _RecordingSearchPort()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _StubLLM()
    app.dependency_overrides[get_doc_search_port] = lambda: search

    _create_user(db_session, UserRole.admin, "admin@help.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "admin@help.test")
        resp = client.post("/nl/help", json={"message": "detalhes internos"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    assert search.received_roles == ["public", "internal"]


# ---------------------------------------------------------------------------
# (d) Search port unavailable → 503
# ---------------------------------------------------------------------------

def test_search_unavailable_gets_503(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: _StubLLM()
    app.dependency_overrides[get_doc_search_port] = lambda: None  # unavailable

    _create_user(db_session, UserRole.agent, "agent@help.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "agent@help.test")
        resp = client.post("/nl/help", json={"message": "teste"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 503


def test_llm_unavailable_gets_503(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_llm_client] = lambda: None  # unavailable
    app.dependency_overrides[get_doc_search_port] = lambda: _RecordingSearchPort()

    _create_user(db_session, UserRole.agent, "agent2@help.test")
    with TestClient(app) as client:
        headers = _token_headers(client, "agent2@help.test")
        resp = client.post("/nl/help", json={"message": "teste"}, headers=headers)

    app.dependency_overrides.clear()
    assert resp.status_code == 503
