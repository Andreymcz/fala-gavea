from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.comment import Comment


class ICommentRepository(ABC):
    @abstractmethod
    def add(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def delete(self, comment_id: str) -> None: ...

    @abstractmethod
    def find_by_id(self, comment_id: str) -> Comment | None: ...

    @abstractmethod
    def list_by_forwarding(self, forwarding_id: str) -> list[Comment]: ...
