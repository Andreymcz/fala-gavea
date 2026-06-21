from __future__ import annotations

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository


class ListSavedFilters:
    def __init__(self, repo: ISavedFilterRepository) -> None:
        self._repo = repo

    def execute(self, owner_id: str) -> list[SavedFilter]:
        return self._repo.find_all_for_user(owner_id)
