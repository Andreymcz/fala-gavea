from abc import ABC, abstractmethod

from fala_gavea.domain.entities.saved_filter import SavedFilter


class ISavedFilterRepository(ABC):
    @abstractmethod
    def save(self, sf: SavedFilter) -> SavedFilter: ...

    @abstractmethod
    def find_by_id(self, id: str) -> SavedFilter | None: ...

    @abstractmethod
    def find_all_for_user(self, owner_id: str) -> list[SavedFilter]: ...

    @abstractmethod
    def update(self, sf: SavedFilter) -> SavedFilter: ...

    @abstractmethod
    def delete(self, id: str) -> None: ...
