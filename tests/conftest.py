from __future__ import annotations

import os

# Must be set before any fala_gavea imports that instantiate JWTService
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import (  # noqa: E402
    SQLAlchemyReportTypeRepository,
)
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import (  # noqa: E402
    SQLAlchemyUserRepository,
)
from fala_gavea.presentation.api.dependencies import get_db  # noqa: E402
from fala_gavea.presentation.api.main import create_app  # noqa: E402
from fala_gavea.domain.entities.report_type import ReportType  # noqa: E402
from fala_gavea.domain.entities.user import User, UserRole  # noqa: E402
from fala_gavea.infrastructure.auth.password_service import PasswordService  # noqa: E402

import uuid
from datetime import datetime, UTC


@pytest.fixture(autouse=True)
def reset_db() -> None:
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
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_report_type(db_session) -> str:
    """Insert a ReportType and return its id."""
    rt = ReportType(
        id=str(uuid.uuid4()),
        name="Iluminacao publica",
        description=None,
        active=True,
        created_at=datetime.now(UTC),
    )
    repo = SQLAlchemyReportTypeRepository(db_session)
    saved = repo.save(rt)
    return saved.id


@pytest.fixture
def citizen_token(client) -> str:
    """Register a citizen and return JWT token."""
    client.post("/auth/register", json={"email": "citizen@test.com", "password": "pass1234", "name": "Test Citizen"})
    resp = client.post("/auth/token", data={"username": "citizen@test.com", "password": "pass1234"})
    return resp.json()["access_token"]


@pytest.fixture
def citizen_headers(citizen_token) -> dict:
    return {"Authorization": f"Bearer {citizen_token}"}


@pytest.fixture
def agent_headers(db_session, client) -> dict:
    """Create an agent user directly in DB (bypasses register which defaults to citizen)."""
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email="agent@test.com",
        password_hash=ps.hash_password("agentpass"),
        name="Test Agent",
        role=UserRole.agent,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(user)
    resp = client.post("/auth/token", data={"username": "agent@test.com", "password": "agentpass"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db_session, client) -> dict:
    """Create an admin user directly in DB and return JWT headers."""
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email="admin@test.com",
        password_hash=ps.hash_password("adminpass"),
        name="Test Admin",
        role=UserRole.admin,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(user)
    resp = client.post("/auth/token", data={"username": "admin@test.com", "password": "adminpass"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
