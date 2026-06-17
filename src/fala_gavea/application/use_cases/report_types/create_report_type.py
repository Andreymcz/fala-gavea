from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository


class CreateReportType:
    def __init__(self, repo: IReportTypeRepository) -> None:
        self._repo = repo

    def execute(self, name: str, description: str | None) -> ReportType:
        name = name.strip()
        if not (3 <= len(name) <= 100):
            raise InvalidInputError("name must be 3-100 characters")
        rt = ReportType(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            active=True,
            created_at=datetime.now(UTC),
        )
        return self._repo.save(rt)
