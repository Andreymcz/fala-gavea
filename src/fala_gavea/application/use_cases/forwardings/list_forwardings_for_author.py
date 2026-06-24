from __future__ import annotations

from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository


class ListForwardingsForAuthor:
    def __init__(
        self,
        forwarding_repo: IForwardingRepository,
        report_repo: IReportRepository,
    ) -> None:
        self._forwarding_repo = forwarding_repo
        self._report_repo = report_repo

    def execute(self, author_id: str) -> list[tuple[Forwarding, list[Report]]]:
        forwardings = self._forwarding_repo.find_by_author_id(author_id)
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
