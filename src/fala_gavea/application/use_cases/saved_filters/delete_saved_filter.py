from __future__ import annotations

from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository
from fala_gavea.application.use_cases.saved_filters.get_saved_filter import GetSavedFilter


class DeleteSavedFilter:
    def __init__(self, repo: ISavedFilterRepository) -> None:
        self._repo = repo
        self._get = GetSavedFilter(repo)

    def execute(self, id: str, owner_id: str) -> None:
        self._get.execute(id, owner_id)  # ownership check; raises if not found/wrong owner
        self._repo.delete(id)
