from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.report import Report, TerritoryLevel
from ...domain.exceptions import InvalidInputError
from ...domain.repositories.report_repository import ReportRepository


@dataclass
class CreateReportInput:
    text: str
    territory_level: str
    territory_name: str
    author_id: str


class CreateReport:
    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    def execute(self, input: CreateReportInput) -> Report:
        if not input.text or len(input.text.strip()) < 5:
            raise InvalidInputError("text must be at least 5 characters")
        try:
            level = TerritoryLevel(input.territory_level)
        except ValueError:
            raise InvalidInputError(
                f"invalid territory_level: {input.territory_level!r}"
            )
        entity = Report.create(
            text=input.text.strip(),
            territory_level=level,
            territory_name=input.territory_name,
            author_id=input.author_id,
        )
        return self._repo.save(entity)
