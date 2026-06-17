from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> User: ...

    @abstractmethod
    def find_by_id(self, id: str) -> User | None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...
