from __future__ import annotations

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.exceptions import SavedFilterNotFoundError
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository


class GetSavedFilter:
    def __init__(self, repo: ISavedFilterRepository) -> None:
        self._repo = repo

    def execute(self, id: str, owner_id: str) -> SavedFilter:
        sf = self._repo.find_by_id(id)
        if sf is None or sf.owner_id != owner_id:
            raise SavedFilterNotFoundError(id)
        return sf
