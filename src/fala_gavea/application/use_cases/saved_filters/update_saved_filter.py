from __future__ import annotations

from datetime import UTC, datetime

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository
from fala_gavea.application.use_cases.saved_filters.get_saved_filter import GetSavedFilter


class UpdateSavedFilter:
    def __init__(self, repo: ISavedFilterRepository) -> None:
        self._repo = repo
        self._get = GetSavedFilter(repo)

    def execute(
        self,
        id: str,
        owner_id: str,
        name: str | None = None,
        body: str | None = None,
    ) -> SavedFilter:
        sf = self._get.execute(id, owner_id)
        if name is not None:
            name = name.strip()
            if not name or len(name) > 80:
                raise InvalidInputError(
                    "name must be between 1 and 80 characters (after trimming)"
                )
            sf.name = name
        if body is not None:
            sf.body = body
        sf.updated_at = datetime.now(UTC)
        return self._repo.update(sf)
