from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fala_gavea.domain.entities.report import Report, Urgency
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer

_log = logging.getLogger(__name__)


@dataclass
class BulkResult:
    inserted: int
    skipped: int
    errors: list[dict] = field(default_factory=list)


class BulkCreateReports:
    def execute(
        self,
        rows: list[dict],
        author_id: str,
        report_type_repo: IReportTypeRepository,
        report_repo: IReportRepository,
        indexer: IReportIndexer | None = None,
    ) -> BulkResult:
        inserted = 0
        skipped = 0
        errors: list[dict] = []

        for i, row in enumerate(rows):
            topico = row.get("topico", "").strip()
            rt = report_type_repo.find_by_name(topico)
            if rt is None:
                skipped += 1
                errors.append({"row": i, "reason": f"ReportType not found: {topico!r}"})
                continue

            text = str(row.get("descricao", "")).strip()
            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except (KeyError, TypeError, ValueError) as exc:
                skipped += 1
                errors.append({"row": i, "reason": f"Invalid coordinates: {exc}"})
                continue

            created_at: datetime | None = row.get("data")
            if created_at is not None and not isinstance(created_at, datetime):
                try:
                    parsed = datetime.fromisoformat(str(created_at))
                    created_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
                except ValueError:
                    created_at = None

            report = Report.create(
                text=text,
                lat=lat,
                lon=lon,
                urgency=Urgency.media,
                report_type_id=rt.id,
                author_id=author_id,
                created_at=created_at,
            )
            report_repo.save(report)
            inserted += 1

            if indexer is not None:
                try:
                    indexer.index(report)
                except Exception as exc:
                    _log.warning("Failed to index report %s: %s", report.id, exc)

        return BulkResult(inserted=inserted, skipped=skipped, errors=errors)
