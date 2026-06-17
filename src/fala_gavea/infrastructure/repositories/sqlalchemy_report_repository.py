from __future__ import annotations

from sqlalchemy.orm import Session

from ...domain.entities.report import Report, TerritoryLevel
from ...domain.repositories.report_repository import ReportRepository
from ..database.models import ReportModel


class SQLAlchemyReportRepository(ReportRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entity: Report) -> Report:
        model = self._to_model(entity)
        self._session.merge(model)
        self._session.commit()
        return entity

    def find_by_id(self, id: str) -> Report | None:
        model = self._session.get(ReportModel, id)
        return self._to_entity(model) if model else None

    def find_all(self, limit: int = 50, offset: int = 0) -> list[Report]:
        models = (
            self._session.query(ReportModel)
            .order_by(ReportModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._session.get(ReportModel, id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.commit()
        return True

    @staticmethod
    def _to_entity(model: ReportModel) -> Report:
        return Report(
            id=model.id,
            text=model.text,
            territory_level=TerritoryLevel(model.territory_level),
            territory_name=model.territory_name,
            author_id=model.author_id,
            created_at=model.created_at,
            ai_labels=model.ai_labels or [],
            label_feedback=model.label_feedback or {},
            likes_count=model.likes_count or 0,
        )

    @staticmethod
    def _to_model(entity: Report) -> ReportModel:
        return ReportModel(
            id=entity.id,
            text=entity.text,
            territory_level=entity.territory_level,
            territory_name=entity.territory_name,
            author_id=entity.author_id,
            created_at=entity.created_at,
            ai_labels=entity.ai_labels,
            label_feedback=entity.label_feedback,
            likes_count=entity.likes_count,
        )
