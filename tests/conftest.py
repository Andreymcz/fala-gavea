import os

# Set DATABASE_URL before any package imports so session.py uses in-memory SQLite.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the database session module so we can monkey-patch it.
# StaticPool forces SQLAlchemy to reuse a single connection, so all sessions
# share the same in-memory SQLite database (avoids per-connection isolation).
import fala_gavea.infrastructure.database.session as _db_mod

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db_mod.engine = _TEST_ENGINE
_db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)

from fala_gavea.infrastructure.database.session import Base  # noqa: E402
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import (  # noqa: E402
    SQLAlchemyReportRepository,
)
from fala_gavea.presentation.api.dependencies import get_report_repo  # noqa: E402
from fala_gavea.presentation.api.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db() -> None:
    """Drop and recreate all tables before each test for full isolation."""
    Base.metadata.drop_all(_TEST_ENGINE)
    Base.metadata.create_all(_TEST_ENGINE)


@pytest.fixture
def db_session():
    session = _db_mod.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def repo(db_session):
    return SQLAlchemyReportRepository(db_session)


@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_report_repo] = (
        lambda: SQLAlchemyReportRepository(db_session)
    )
    return TestClient(app)
