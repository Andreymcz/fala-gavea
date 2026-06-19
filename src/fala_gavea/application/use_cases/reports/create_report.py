from __future__ import annotations

import logging

from fala_gavea.domain.entities.report import Report, Urgency
from fala_gavea.domain.exceptions import InvalidInputError, ReportTypeNotFoundError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer

_log = logging.getLogger(__name__)


class CreateReport:
    def __init__(
        self,
        report_repo: IReportRepository,
        report_type_repo: IReportTypeRepository,
        indexer: IReportIndexer | None = None,
    ) -> None:
        self._report_repo = report_repo
        self._report_type_repo = report_type_repo
        self._indexer = indexer

    def execute(
        self,
        text: str,
        lat: float,
        lon: float,
        urgency: str,
        report_type_id: str,
        author_id: str,
        photo_url: str | None = None,
    ) -> Report:
        text = text.strip()
        if len(text) < 10 or len(text) > 2000:
            raise InvalidInputError("text must be 10-2000 characters")
        if not (-90.0 <= lat <= 90.0):
            raise InvalidInputError("lat must be between -90 and 90")
        if not (-180.0 <= lon <= 180.0):
            raise InvalidInputError("lon must be between -180 and 180")
        rt = self._report_type_repo.find_by_id(report_type_id)
        if rt is None or not rt.active:
            raise ReportTypeNotFoundError(f"ReportType not found or inactive: {report_type_id}")
        report = self._report_repo.save(
            Report.create(text, lat, lon, Urgency(urgency), report_type_id, author_id, photo_url)
        )
        if self._indexer is not None:
            try:
                self._indexer.index(report)
            except Exception as exc:
                _log.warning("Failed to index report %s: %s", report.id, exc)
        return report
