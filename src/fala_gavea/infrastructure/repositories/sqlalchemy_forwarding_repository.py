from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.repositories.forwarding_repository import (
    ForwardingFilters,
    IForwardingRepository,
)
from fala_gavea.infrastructure.database.models import (
    ForwardingModel,
    ForwardingReportModel,
)


class SQLAlchemyForwardingRepository(IForwardingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, f: Forwarding) -> Forwarding:
        model = self._session.get(ForwardingModel, f.id)
        if model is None:
            model = ForwardingModel(
                id=f.id,
                institution=f.institution,
                proposed_solution=f.proposed_solution,
                status=f.status.value,
                agent_id=f.agent_id,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
            self._session.add(model)
        else:
            model.institution = f.institution
            model.proposed_solution = f.proposed_solution
            model.status = f.status.value
            model.updated_at = f.updated_at
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, id: str) -> Forwarding | None:
        model = self._session.get(ForwardingModel, id)
        return self._to_entity(model) if model else None

    def find_all(self, filters: ForwardingFilters) -> list[Forwarding]:
        stmt = select(ForwardingModel)
        if filters.status is not None:
            stmt = stmt.where(ForwardingModel.status == filters.status.value)
        if filters.institution is not None:
            stmt = stmt.where(
                ForwardingModel.institution.ilike(f"%{filters.institution}%")
            )
        if filters.agent_id is not None:
            stmt = stmt.where(ForwardingModel.agent_id == filters.agent_id)
        if filters.since is not None:
            stmt = stmt.where(ForwardingModel.created_at >= filters.since)
        if filters.until is not None:
            stmt = stmt.where(ForwardingModel.created_at <= filters.until)
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def add_reports(self, forwarding_id: str, report_ids: list[str]) -> None:
        for rid in report_ids:
            self._session.add(
                ForwardingReportModel(forwarding_id=forwarding_id, report_id=rid)
            )
        self._session.commit()

    def get_report_ids(self, forwarding_id: str) -> list[str]:
        stmt = select(ForwardingReportModel.report_id).where(
            ForwardingReportModel.forwarding_id == forwarding_id
        )
        return list(self._session.scalars(stmt).all())

    def _to_entity(self, m: ForwardingModel) -> Forwarding:
        return Forwarding(
            id=m.id,
            institution=m.institution,
            proposed_solution=m.proposed_solution,
            status=ForwardingStatus(m.status),
            agent_id=m.agent_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
