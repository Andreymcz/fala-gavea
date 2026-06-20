from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.report_type import ReportType


class IReportTypeRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: str) -> ReportType | None: ...

    @abstractmethod
    def find_all_active(self) -> list[ReportType]: ...

    @abstractmethod
    def find_by_name(self, name: str) -> ReportType | None: ...

    @abstractmethod
    def save(self, rt: ReportType) -> ReportType: ...
