from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fala_gavea.application.use_cases.forwardings.create_forwarding import CreateForwarding
from fala_gavea.application.use_cases.forwardings.get_forwarding import GetForwarding
from fala_gavea.application.use_cases.forwardings.list_forwardings import ListForwardings
from fala_gavea.application.use_cases.forwardings.update_forwarding import UpdateForwarding
from fala_gavea.application.use_cases.forwardings.update_forwarding_status import UpdateForwardingStatus
from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError
from fala_gavea.domain.repositories.forwarding_repository import ForwardingFilters, IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.presentation.api.dependencies import (
    get_forwarding_repo,
    get_report_repo,
    require_any_role,
)
from fala_gavea.presentation.schemas.forwarding import (
    ForwardingCreate,
    ForwardingResponse,
    ForwardingStatusUpdate,
    ForwardingUpdate,
    PublicForwardingResponse,
    ReportSummary,
)

router = APIRouter()

_agent_or_admin = require_any_role("agent", "admin")


def _build_response(forwarding: Forwarding, reports: list[Report]) -> ForwardingResponse:
    return ForwardingResponse(
        id=forwarding.id,
        institution=forwarding.institution,
        proposed_solution=forwarding.proposed_solution,
        status=forwarding.status.value,
        agent_id=forwarding.agent_id,
        reports=[
            ReportSummary(
                id=r.id,
                text=r.text,
                urgency=r.urgency.value,
                status=r.status.value,
                report_type_id=r.report_type_id,
                created_at=r.created_at,
            )
            for r in reports
        ],
        created_at=forwarding.created_at,
        updated_at=forwarding.updated_at,
    )


def _build_public_response(forwarding: Forwarding, reports: list[Report]) -> PublicForwardingResponse:
    return PublicForwardingResponse(
        id=forwarding.id,
        institution=forwarding.institution,
        proposed_solution=forwarding.proposed_solution,
        status=forwarding.status.value,
        reports=[
            ReportSummary(
                id=r.id,
                text=r.text,
                urgency=r.urgency.value,
                status=r.status.value,
                report_type_id=r.report_type_id,
                created_at=r.created_at,
            )
            for r in reports
        ],
        created_at=forwarding.created_at,
        updated_at=forwarding.updated_at,
    )


# Registered before GET /{id} so FastAPI does not match "/public" against "/{id}".
@router.get("/public", response_model=list[PublicForwardingResponse])
def list_public_forwardings(
    status_filter: str | None = Query(None, alias="status"),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> list[PublicForwardingResponse]:
    parsed_status: ForwardingStatus | None = None
    if status_filter is not None:
        try:
            parsed_status = ForwardingStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {status_filter}",
            )

    filters = ForwardingFilters(status=parsed_status)
    forwardings = ListForwardings(forwarding_repo).execute(filters)

    result: list[PublicForwardingResponse] = []
    for fwd in forwardings:
        try:
            _, reports = GetForwarding(forwarding_repo, report_repo).execute(fwd.id)
        except ForwardingNotFoundError:
            reports = []
        result.append(_build_public_response(fwd, reports))
    return result


@router.get("/public/{id}", response_model=PublicForwardingResponse)
def get_public_forwarding(
    id: str,
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> PublicForwardingResponse:
    try:
        forwarding, reports = GetForwarding(forwarding_repo, report_repo).execute(id)
        return _build_public_response(forwarding, reports)
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=ForwardingResponse, status_code=status.HTTP_201_CREATED)
def create_forwarding(
    body: ForwardingCreate,
    current_user: User = Depends(_agent_or_admin),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> ForwardingResponse:
    try:
        forwarding, reports = CreateForwarding(forwarding_repo, report_repo).execute(
            institution=body.institution,
            proposed_solution=body.proposed_solution,
            report_ids=body.report_ids,
            agent_id=current_user.id,
        )
        return _build_response(forwarding, reports)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=list[ForwardingResponse])
def list_forwardings(
    status_filter: str | None = Query(None, alias="status"),
    institution: str | None = Query(None),
    agent_id: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    _current_user: User = Depends(_agent_or_admin),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> list[ForwardingResponse]:
    parsed_status: ForwardingStatus | None = None
    if status_filter is not None:
        try:
            parsed_status = ForwardingStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status: {status_filter}",
            )

    filters = ForwardingFilters(
        status=parsed_status,
        institution=institution,
        agent_id=agent_id,
        since=since,
        until=until,
    )
    forwardings = ListForwardings(forwarding_repo).execute(filters)

    result: list[ForwardingResponse] = []
    for fwd in forwardings:
        try:
            _, reports = GetForwarding(forwarding_repo, report_repo).execute(fwd.id)
        except ForwardingNotFoundError:
            reports = []
        result.append(_build_response(fwd, reports))
    return result


@router.get("/{id}", response_model=ForwardingResponse)
def get_forwarding(
    id: str,
    _current_user: User = Depends(_agent_or_admin),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> ForwardingResponse:
    try:
        forwarding, reports = GetForwarding(forwarding_repo, report_repo).execute(id)
        return _build_response(forwarding, reports)
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{id}/status", response_model=ForwardingResponse)
def update_forwarding_status(
    id: str,
    body: ForwardingStatusUpdate,
    _current_user: User = Depends(_agent_or_admin),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> ForwardingResponse:
    try:
        forwarding = UpdateForwardingStatus(forwarding_repo).execute(id, body.status)
        report_ids = forwarding_repo.get_report_ids(forwarding.id)
        reports = [
            r
            for rid in report_ids
            if (r := report_repo.find_by_id(rid)) is not None
        ]
        return _build_response(forwarding, reports)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{id}", response_model=ForwardingResponse)
def update_forwarding(
    id: str,
    body: ForwardingUpdate,
    _current_user: User = Depends(_agent_or_admin),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> ForwardingResponse:
    try:
        forwarding = UpdateForwarding(forwarding_repo).execute(
            id,
            institution=body.institution,
            proposed_solution=body.proposed_solution,
        )
        report_ids = forwarding_repo.get_report_ids(forwarding.id)
        reports = [
            r
            for rid in report_ids
            if (r := report_repo.find_by_id(rid)) is not None
        ]
        return _build_response(forwarding, reports)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
