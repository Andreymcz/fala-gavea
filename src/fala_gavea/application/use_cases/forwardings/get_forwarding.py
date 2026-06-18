from __future__ import annotations

from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import ForwardingNotFoundError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository


class GetForwarding:
    def __init__(
        self,
        forwarding_repo: IForwardingRepository,
        report_repo: IReportRepository,
    ) -> None:
        self._forwarding_repo = forwarding_repo
        self._report_repo = report_repo

    def execute(self, id: str) -> tuple[Forwarding, list[Report]]:
        forwarding = self._forwarding_repo.find_by_id(id)
        if forwarding is None:
            raise ForwardingNotFoundError(id)

        report_ids = self._forwarding_repo.get_report_ids(id)
        reports = [
            r
            for rid in report_ids
            if (r := self._report_repo.find_by_id(rid)) is not None
        ]
        return (forwarding, reports)
