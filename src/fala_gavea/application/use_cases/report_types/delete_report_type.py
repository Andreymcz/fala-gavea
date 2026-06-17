from __future__ import annotations

from fala_gavea.domain.exceptions import ReportTypeNotFoundError
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository


class DeleteReportType:
    def __init__(self, repo: IReportTypeRepository) -> None:
        self._repo = repo

    def execute(self, id: str) -> None:
        rt = self._repo.find_by_id(id)
        if rt is None:
            raise ReportTypeNotFoundError(id)
        rt.active = False
        self._repo.save(rt)
