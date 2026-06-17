from __future__ import annotations

from ...domain.exceptions import ReportNotFoundError
from ...domain.repositories.report_repository import ReportRepository


class DeleteReport:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    def execute(self, id: str) -> None:
        deleted = self._repo.delete(id)
        if not deleted:
            raise ReportNotFoundError(id)
