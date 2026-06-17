from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.infrastructure.database.models import ReportTypeModel


class SQLAlchemyReportTypeRepository(IReportTypeRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_id(self, id: str) -> ReportType | None:
        model = self._session.get(ReportTypeModel, id)
        return self._to_entity(model) if model else None

    def find_all_active(self) -> list[ReportType]:
        stmt = select(ReportTypeModel).where(ReportTypeModel.active == True)  # noqa: E712
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def save(self, rt: ReportType) -> ReportType:
        model = self._session.get(ReportTypeModel, rt.id)
        if model is None:
            model = self._to_model(rt)
            self._session.add(model)
        else:
            model.name = rt.name
            model.description = rt.description
            model.active = rt.active
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def _to_model(self, rt: ReportType) -> ReportTypeModel:
        return ReportTypeModel(
            id=rt.id,
            name=rt.name,
            description=rt.description,
            active=rt.active,
            created_at=rt.created_at,
        )

    def _to_entity(self, model: ReportTypeModel) -> ReportType:
        return ReportType(
            id=model.id,
            name=model.name,
            description=model.description,
            active=model.active,
            created_at=model.created_at,
        )
