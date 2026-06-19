from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.reports.create_report import CreateReport
from fala_gavea.application.use_cases.reports.get_report import GetReport
from fala_gavea.application.use_cases.reports.list_reports_geojson import ListReportsGeoJSON
from fala_gavea.domain.entities.report import ReportStatus, Urgency
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidInputError, ReportNotFoundError, ReportTypeNotFoundError
from fala_gavea.domain.repositories.report_repository import ReportFilters
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_report_indexer,
    get_report_repo,
    get_report_type_repo,
)
from fala_gavea.presentation.schemas.report import ReportCreate, ReportFiltersQuery, ReportResponse

router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ReportCreate,
    current_user: User = Depends(get_current_user),
    report_repo=Depends(get_report_repo),
    report_type_repo=Depends(get_report_type_repo),
    indexer: IReportIndexer | None = Depends(get_report_indexer),
) -> ReportResponse:
    try:
        report = CreateReport(report_repo, report_type_repo, indexer=indexer).execute(
            text=body.text,
            lat=body.lat,
            lon=body.lon,
            urgency=body.urgency,
            report_type_id=body.report_type_id,
            author_id=current_user.id,
            photo_url=body.photo_url,
        )
        return ReportResponse(
            id=report.id,
            text=report.text,
            lat=report.lat,
            lon=report.lon,
            urgency=report.urgency.value,
            status=report.status.value,
            report_type_id=report.report_type_id,
            author_id=report.author_id,
            photo_url=report.photo_url,
            created_at=report.created_at,
        )
    except (InvalidInputError, ReportTypeNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/geojson")
def list_reports_geojson(
    q: ReportFiltersQuery = Depends(),
    report_repo=Depends(get_report_repo),
) -> dict:
    bbox = None
    if q.bbox:
        try:
            parts = [float(x) for x in q.bbox.split(",")]
            if len(parts) != 4:
                raise ValueError
            bbox = tuple(parts)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="bbox must be 'minLat,minLon,maxLat,maxLon'",
            )
    filters = ReportFilters(
        report_type_id=q.type_id,
        urgency=Urgency(q.urgency) if q.urgency else None,
        status=ReportStatus(q.status) if q.status else None,
        since=q.since,
        until=q.until,
        bbox=bbox,
    )
    return ListReportsGeoJSON(report_repo).execute(filters)


@router.get("/{id}", response_model=ReportResponse)
def get_report(
    id: str,
    current_user: User = Depends(get_current_user),
    report_repo=Depends(get_report_repo),
) -> ReportResponse:
    try:
        report = GetReport(report_repo).execute(id)
        return ReportResponse(
            id=report.id,
            text=report.text,
            lat=report.lat,
            lon=report.lon,
            urgency=report.urgency.value,
            status=report.status.value,
            report_type_id=report.report_type_id,
            author_id=report.author_id,
            photo_url=report.photo_url,
            created_at=report.created_at,
        )
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
