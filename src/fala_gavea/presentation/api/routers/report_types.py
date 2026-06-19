from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from fala_gavea.application.use_cases.report_types.create_report_type import CreateReportType
from fala_gavea.application.use_cases.report_types.delete_report_type import DeleteReportType
from fala_gavea.application.use_cases.report_types.update_report_type import UpdateReportType
from fala_gavea.domain.exceptions import InvalidInputError, ReportTypeNotFoundError
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.presentation.api.dependencies import get_report_type_repo, require_role
from fala_gavea.presentation.schemas.report_type import (
    ReportTypeCreate,
    ReportTypeResponse,
    ReportTypeUpdate,
)

router = APIRouter()


@router.get("/", response_model=list[ReportTypeResponse])
def list_report_types(
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
) -> list[ReportTypeResponse]:
    types = report_type_repo.find_all_active()
    return [ReportTypeResponse.model_validate(rt) for rt in types]


@router.post("/", response_model=ReportTypeResponse, status_code=status.HTTP_201_CREATED)
def create_report_type(
    body: ReportTypeCreate,
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
) -> ReportTypeResponse:
    try:
        rt = CreateReportType(report_type_repo).execute(body.name, body.description)
        return ReportTypeResponse.model_validate(rt)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch("/{id}", response_model=ReportTypeResponse)
def update_report_type(
    id: str,
    body: ReportTypeUpdate,
    _current_user=Depends(require_role("admin")),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
) -> ReportTypeResponse:
    try:
        rt = UpdateReportType(report_type_repo).execute(id, body.name, body.description)
        return ReportTypeResponse.model_validate(rt)
    except ReportTypeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_type(
    id: str,
    _current_user=Depends(require_role("admin")),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
) -> Response:
    try:
        DeleteReportType(report_type_repo).execute(id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ReportTypeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
