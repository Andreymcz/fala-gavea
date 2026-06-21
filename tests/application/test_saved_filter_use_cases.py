from __future__ import annotations

import os

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fala_gavea.infrastructure.database.models import Base
from fala_gavea.infrastructure.repositories.sqlalchemy_saved_filter_repository import (
    SQLAlchemySavedFilterRepository,
)
from fala_gavea.application.use_cases.saved_filters.create_saved_filter import CreateSavedFilter
from fala_gavea.application.use_cases.saved_filters.get_saved_filter import GetSavedFilter
from fala_gavea.application.use_cases.saved_filters.list_saved_filters import ListSavedFilters
from fala_gavea.application.use_cases.saved_filters.update_saved_filter import UpdateSavedFilter
from fala_gavea.application.use_cases.saved_filters.delete_saved_filter import DeleteSavedFilter
from fala_gavea.domain.exceptions import InvalidInputError, SavedFilterNotFoundError


@pytest.fixture
def repo():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield SQLAlchemySavedFilterRepository(sess)
    sess.close()
    Base.metadata.drop_all(engine)


BODY = '{"status": "pendente"}'


def test_create_then_get(repo):
    sf = CreateSavedFilter(repo).execute("user-1", "My Filter", BODY)
    fetched = GetSavedFilter(repo).execute(sf.id, "user-1")
    assert fetched.id == sf.id
    assert fetched.name == "My Filter"
    assert fetched.owner_id == "user-1"


def test_get_wrong_owner_raises_not_found(repo):
    sf = CreateSavedFilter(repo).execute("user-1", "Filter", BODY)
    with pytest.raises(SavedFilterNotFoundError):
        GetSavedFilter(repo).execute(sf.id, "user-2")


def test_update_patches_name_and_body(repo):
    sf = CreateSavedFilter(repo).execute("user-1", "Original", BODY)
    updated = UpdateSavedFilter(repo).execute(
        sf.id, "user-1", name="Updated", body='{"status": "resolvido"}'
    )
    assert updated.name == "Updated"
    assert updated.body == '{"status": "resolvido"}'
    # Confirm persisted
    fetched = GetSavedFilter(repo).execute(sf.id, "user-1")
    assert fetched.name == "Updated"


def test_delete_removes_entry(repo):
    sf = CreateSavedFilter(repo).execute("user-1", "ToDelete", BODY)
    DeleteSavedFilter(repo).execute(sf.id, "user-1")
    with pytest.raises(SavedFilterNotFoundError):
        GetSavedFilter(repo).execute(sf.id, "user-1")


def test_list_returns_only_own(repo):
    CreateSavedFilter(repo).execute("user-1", "A", BODY)
    CreateSavedFilter(repo).execute("user-1", "B", BODY)
    CreateSavedFilter(repo).execute("user-2", "Other", BODY)
    results = ListSavedFilters(repo).execute("user-1")
    assert len(results) == 2
    assert all(r.owner_id == "user-1" for r in results)


def test_create_name_too_long_raises_invalid_input(repo):
    with pytest.raises(InvalidInputError):
        CreateSavedFilter(repo).execute("user-1", "x" * 81, BODY)


def test_create_empty_name_raises_invalid_input(repo):
    with pytest.raises(InvalidInputError):
        CreateSavedFilter(repo).execute("user-1", "   ", BODY)
