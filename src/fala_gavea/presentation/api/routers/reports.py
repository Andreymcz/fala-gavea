from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.create_report import CreateReport, CreateReportInput
from fala_gavea.application.use_cases.delete_report import DeleteReport
from fala_gavea.application.use_cases.get_report import GetReport
from fala_gavea.application.use_cases.list_reports import ListReports
from fala_gavea.domain.exceptions import ReportNotFoundError, InvalidInputError
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import (
    SQLAlchemyReportRepository,
)
from fala_gavea.presentation.api.dependencies import get_report_repo
from fala_gavea.presentation.schemas.report_schemas import ReportCreate, ReportResponse

router = APIRouter()


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ReportCreate,
    repo: SQLAlchemyReportRepository = Depends(get_report_repo),
) -> ReportResponse:
    try:
        entity = CreateReport(repo).execute(
            CreateReportInput(
                text=body.text,
                territory_level=body.territory_level,
                territory_name=body.territory_name,
                author_id=body.author_id,
            )
        )
        return ReportResponse(**entity.__dict__)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    limit: int = 50,
    offset: int = 0,
    repo: SQLAlchemyReportRepository = Depends(get_report_repo),
) -> list[ReportResponse]:
    entities = ListReports(repo).execute(limit=limit, offset=offset)
    return [ReportResponse(**e.__dict__) for e in entities]


@router.get("/{id}", response_model=ReportResponse)
def get_report(
    id: str,
    repo: SQLAlchemyReportRepository = Depends(get_report_repo),
) -> ReportResponse:
    try:
        entity = GetReport(repo).execute(id)
        return ReportResponse(**entity.__dict__)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    id: str,
    repo: SQLAlchemyReportRepository = Depends(get_report_repo),
) -> None:
    try:
        DeleteReport(repo).execute(id)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
