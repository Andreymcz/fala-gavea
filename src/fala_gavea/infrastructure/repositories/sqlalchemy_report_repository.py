from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus
from fala_gavea.domain.repositories.report_repository import IReportRepository, ReportFilters
from fala_gavea.infrastructure.database.models import ReportModel


class SQLAlchemyReportRepository(IReportRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, report: Report) -> Report:
        model = self._session.get(ReportModel, report.id)
        if model is None:
            model = self._to_model(report)
            self._session.add(model)
        else:
            # update existing
            model.text = report.text
            model.lat = report.lat
            model.lon = report.lon
            model.urgency = report.urgency.value
            model.photo_url = report.photo_url
            model.status = report.status.value
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, id: str) -> Report | None:
        model = self._session.get(ReportModel, id)
        return self._to_entity(model) if model else None

    def find_all(self, filters: ReportFilters) -> list[Report]:
        stmt = select(ReportModel)
        if filters.report_type_ids is not None:
            stmt = stmt.where(ReportModel.report_type_id.in_(filters.report_type_ids))
        if filters.urgencies is not None:
            stmt = stmt.where(ReportModel.urgency.in_([u.value for u in filters.urgencies]))
        if filters.statuses is not None:
            stmt = stmt.where(ReportModel.status.in_([s.value for s in filters.statuses]))
        if filters.since is not None:
            stmt = stmt.where(ReportModel.created_at >= filters.since)
        if filters.until is not None:
            stmt = stmt.where(ReportModel.created_at <= filters.until)
        if filters.bbox is not None:
            min_lat, min_lon, max_lat, max_lon = filters.bbox
            stmt = stmt.where(
                ReportModel.lat >= min_lat,
                ReportModel.lat <= max_lat,
                ReportModel.lon >= min_lon,
                ReportModel.lon <= max_lon,
            )
        if filters.text is not None:
            stmt = stmt.where(ReportModel.text.ilike(f"%{filters.text}%"))
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def find_page(
        self,
        filters: ReportFilters,
        *,
        limit: int,
        offset: int,
        order: str = "recent",
        candidate_cap: int = 500,
    ) -> tuple[list[Report], int]:
        from sqlalchemy import func

        stmt = select(ReportModel)
        if filters.report_type_ids is not None:
            stmt = stmt.where(ReportModel.report_type_id.in_(filters.report_type_ids))
        if filters.urgencies is not None:
            stmt = stmt.where(ReportModel.urgency.in_([u.value for u in filters.urgencies]))
        if filters.statuses is not None:
            stmt = stmt.where(ReportModel.status.in_([s.value for s in filters.statuses]))
        if filters.since is not None:
            stmt = stmt.where(ReportModel.created_at >= filters.since)
        if filters.until is not None:
            stmt = stmt.where(ReportModel.created_at <= filters.until)
        if filters.bbox is not None:
            min_lat, min_lon, max_lat, max_lon = filters.bbox
            stmt = stmt.where(
                ReportModel.lat >= min_lat,
                ReportModel.lat <= max_lat,
                ReportModel.lon >= min_lon,
                ReportModel.lon <= max_lon,
            )
        if filters.text is not None:
            stmt = stmt.where(ReportModel.text.ilike(f"%{filters.text}%"))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = self._session.scalar(count_stmt) or 0
        if order == "urgent":
            stmt = stmt.order_by(ReportModel.urgency.desc(), ReportModel.created_at.desc())
        else:
            stmt = stmt.order_by(ReportModel.created_at.desc())
        stmt = stmt.offset(offset).limit(min(limit, candidate_cap))
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()], total

    def _to_model(self, report: Report) -> ReportModel:
        return ReportModel(
            id=report.id,
            text=report.text,
            lat=report.lat,
            lon=report.lon,
            urgency=report.urgency.value,
            photo_url=report.photo_url,
            report_type_id=report.report_type_id,
            author_id=report.author_id,
            status=report.status.value,
            created_at=report.created_at,
        )

    def _to_entity(self, model: ReportModel) -> Report:
        return Report(
            id=model.id,
            text=model.text,
            lat=model.lat,
            lon=model.lon,
            urgency=Urgency(model.urgency),
            photo_url=model.photo_url,
            report_type_id=model.report_type_id,
            author_id=model.author_id,
            status=ReportStatus(model.status),
            created_at=model.created_at,
        )
