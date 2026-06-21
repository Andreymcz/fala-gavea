from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from sqlalchemy import event

from fala_gavea.infrastructure.database.models import Base
from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.infrastructure.repositories.sqlalchemy_saved_filter_repository import (
    SQLAlchemySavedFilterRepository,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Disable FK enforcement so tests don't need to insert real user rows
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()
    Base.metadata.drop_all(engine)


def _make_filter(owner_id: str = "user-1", name: str = "My Filter") -> SavedFilter:
    now = datetime.now(UTC)
    return SavedFilter(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        name=name,
        body='{"status": "pendente"}',
        schema_ver="1",
        created_at=now,
        updated_at=now,
    )


def test_save_returns_entity(session):
    repo = SQLAlchemySavedFilterRepository(session)
    sf = _make_filter()
    result = repo.save(sf)
    assert result.id == sf.id
    assert result.name == sf.name
    assert result.owner_id == sf.owner_id


def test_find_by_id_returns_none_for_missing(session):
    repo = SQLAlchemySavedFilterRepository(session)
    assert repo.find_by_id("nonexistent-id") is None


def test_find_all_for_user_returns_only_own(session):
    repo = SQLAlchemySavedFilterRepository(session)
    sf1 = _make_filter(owner_id="user-1", name="Filter A")
    sf2 = _make_filter(owner_id="user-1", name="Filter B")
    sf_other = _make_filter(owner_id="user-2", name="Other")
    repo.save(sf1)
    repo.save(sf2)
    repo.save(sf_other)

    results = repo.find_all_for_user("user-1")
    assert len(results) == 2
    ids = {r.id for r in results}
    assert sf1.id in ids
    assert sf2.id in ids
    assert sf_other.id not in ids


def test_update_changes_name_and_body(session):
    repo = SQLAlchemySavedFilterRepository(session)
    sf = _make_filter()
    repo.save(sf)

    sf.name = "Updated Name"
    sf.body = '{"status": "resolvido"}'
    result = repo.update(sf)

    assert result.name == "Updated Name"
    assert result.body == '{"status": "resolvido"}'

    fetched = repo.find_by_id(sf.id)
    assert fetched is not None
    assert fetched.name == "Updated Name"


def test_delete_removes_entry(session):
    repo = SQLAlchemySavedFilterRepository(session)
    sf = _make_filter()
    repo.save(sf)

    assert repo.find_by_id(sf.id) is not None
    repo.delete(sf.id)
    assert repo.find_by_id(sf.id) is None
