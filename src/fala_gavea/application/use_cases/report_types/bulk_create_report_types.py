from __future__ import annotations

from dataclasses import dataclass, field

from fala_gavea.application.use_cases.report_types.create_report_type import CreateReportType
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository


@dataclass
class BulkReportTypeResult:
    inserted: int = 0
    skipped: int = 0
    errors: list[dict] = field(default_factory=list)


class BulkCreateReportTypes:
    def execute(self, rows: list[dict], report_type_repo: IReportTypeRepository) -> BulkReportTypeResult:
        result = BulkReportTypeResult()
        for i, row in enumerate(rows):
            nome = (row.get("nome") or "").strip()
            descricao = row.get("descricao") or None

            if report_type_repo.find_by_name(nome) is not None:
                result.skipped += 1
                continue

            try:
                CreateReportType(report_type_repo).execute(nome, descricao)
                result.inserted += 1
            except InvalidInputError as exc:
                result.skipped += 1
                result.errors.append({"row": i + 1, "reason": str(exc)})

        return result
