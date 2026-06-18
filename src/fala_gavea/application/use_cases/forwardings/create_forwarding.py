from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.entities.report import Report, ReportStatus
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository


class CreateForwarding:
    def __init__(
        self,
        forwarding_repo: IForwardingRepository,
        report_repo: IReportRepository,
    ) -> None:
        self._forwarding_repo = forwarding_repo
        self._report_repo = report_repo

    def execute(
        self,
        institution: str,
        proposed_solution: str,
        report_ids: list[str],
        agent_id: str,
    ) -> tuple[Forwarding, list[Report]]:
        institution = institution.strip()
        if not (3 <= len(institution) <= 200):
            raise InvalidInputError("institution must be 3-200 characters")

        proposed_solution = proposed_solution.strip()
        if not (20 <= len(proposed_solution) <= 5000):
            raise InvalidInputError("proposed_solution must be 20-5000 characters")

        if not report_ids:
            raise InvalidInputError("report_ids must not be empty")

        reports: list[Report] = []
        for rid in report_ids:
            report = self._report_repo.find_by_id(rid)
            if report is None:
                raise InvalidInputError(f"Report not found: {rid}")
            reports.append(report)

        now = datetime.now(timezone.utc)
        forwarding = Forwarding(
            id=str(uuid4()),
            institution=institution,
            proposed_solution=proposed_solution,
            status=ForwardingStatus.aguardando_solucao,
            agent_id=agent_id,
            created_at=now,
            updated_at=now,
        )
        self._forwarding_repo.save(forwarding)
        self._forwarding_repo.add_reports(forwarding.id, report_ids)

        for report in reports:
            report.status = ReportStatus.encaminhado
            self._report_repo.save(report)

        return (forwarding, reports)
