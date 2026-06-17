from __future__ import annotations

from abc import ABC, abstractmethod

from ..entities.report import Report


class ReportRepository(ABC):
    @abstractmethod
    def save(self, entity: Report) -> Report: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Report | None: ...

    @abstractmethod
    def find_all(self, limit: int = 50, offset: int = 0) -> list[Report]: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...
