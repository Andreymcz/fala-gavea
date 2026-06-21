from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository


class CreateSavedFilter:
    def __init__(self, repo: ISavedFilterRepository) -> None:
        self._repo = repo

    def execute(self, owner_id: str, name: str, body: str) -> SavedFilter:
        name = name.strip()
        if not name or len(name) > 80:
            raise InvalidInputError(
                "name must be between 1 and 80 characters (after trimming)"
            )
        now = datetime.now(UTC)
        sf = SavedFilter(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            name=name,
            body=body,
            schema_ver="1",
            created_at=now,
            updated_at=now,
        )
        return self._repo.save(sf)
