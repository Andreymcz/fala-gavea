from __future__ import annotations

from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.exceptions import InvalidInputError, ReportTypeNotFoundError
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository


class UpdateReportType:
    def __init__(self, repo: IReportTypeRepository) -> None:
        self._repo = repo

    def execute(self, id: str, name: str | None, description: str | None) -> ReportType:
        rt = self._repo.find_by_id(id)
        if rt is None:
            raise ReportTypeNotFoundError(id)
        if name is not None:
            name = name.strip()
            if not (3 <= len(name) <= 100):
                raise InvalidInputError("name must be 3-100 characters")
            rt.name = name
        if description is not None:
            rt.description = description
        return self._repo.save(rt)
