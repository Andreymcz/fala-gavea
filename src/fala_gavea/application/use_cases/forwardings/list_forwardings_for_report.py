from __future__ import annotations

from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import ReportNotFoundError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository


class ListForwardingsForReport:
    """Reverse lookup (Rec 3): all forwardings linked to a report, each with its
    own linked reports hydrated. Validates the report exists (404 otherwise).
    Returns an empty list when the report exists but has no forwardings."""

    def __init__(
        self,
        forwarding_repo: IForwardingRepository,
        report_repo: IReportRepository,
    ) -> None:
        self._forwarding_repo = forwarding_repo
        self._report_repo = report_repo

    def execute(self, report_id: str) -> list[tuple[Forwarding, list[Report]]]:
        if self._report_repo.find_by_id(report_id) is None:
            raise ReportNotFoundError(f"Report not found: {report_id}")

        forwardings = self._forwarding_repo.find_by_report_id(report_id)
        result: list[tuple[Forwarding, list[Report]]] = []
        for fwd in forwardings:
            report_ids = self._forwarding_repo.get_report_ids(fwd.id)
            reports = [
                r
                for rid in report_ids
                if (r := self._report_repo.find_by_id(rid)) is not None
            ]
            result.append((fwd, reports))
        return result
