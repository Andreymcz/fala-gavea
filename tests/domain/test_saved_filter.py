import pytest
from datetime import datetime

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository


def test_saved_filter_instantiation() -> None:
    now = datetime(2026, 1, 1, 12, 0, 0)
    sf = SavedFilter(
        id="abc123",
        owner_id="user-1",
        name="My Filter",
        body='{"status": "open"}',
        schema_ver="1",
        created_at=now,
        updated_at=now,
    )
    assert sf.id == "abc123"
    assert sf.owner_id == "user-1"
    assert sf.name == "My Filter"
    assert sf.body == '{"status": "open"}'
    assert sf.schema_ver == "1"
    assert sf.created_at == now
    assert sf.updated_at == now


def test_saved_filter_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        ISavedFilterRepository()  # type: ignore[abstract]
