from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fala_gavea.application.use_cases.forwardings.list_forwardings_for_report import (
    ListForwardingsForReport,
)
from fala_gavea.application.use_cases.reports.create_report import CreateReport
from fala_gavea.application.use_cases.reports.find_similar_reports import FindSimilarReports
from fala_gavea.application.use_cases.reports.find_similar_to_report_set import (
    FindSimilarToReportSet,
)
from fala_gavea.application.use_cases.reports.get_report import GetReport
from fala_gavea.application.use_cases.reports.list_reports_geojson import ListReportsGeoJSON
from fala_gavea.application.use_cases.reports.query_reports import QueryReports
from fala_gavea.application.use_cases.reports.search_reports import SearchReports
from fala_gavea.application.use_cases.topics.get_topics_for_reports import GetTopicsForReports
from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidInputError, ReportNotFoundError, ReportTypeNotFoundError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository, ReportFilters
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer, ISemanticSearchPort, ITopicModelPort
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_forwarding_repo,
    get_keyword_extractor,
    get_report_indexer,
    get_report_repo,
    get_report_type_repo,
    get_semantic_search_port,
    require_any_role,
    require_role,
)
from fala_gavea.presentation.schemas.forwarding import PublicForwardingResponse, ReportSummary
from fala_gavea.presentation.schemas.keyword import KeywordItem, KeywordListResponse
from fala_gavea.presentation.schemas.report import (
    ReportCreate,
    ReportFiltersQuery,
    ReportQueryItem,
    ReportQueryRequest,
    ReportQueryResponse,
    ReportResponse,
    ReportSearchResult,
    ReportSetSimilarRequest,
)

router = APIRouter()

_agent_or_admin = require_any_role("agent", "admin")


def _parse_bbox(q: ReportFiltersQuery) -> tuple[float, float, float, float] | None:
    if not q.bbox:
        return None
    try:
        parts = [float(x) for x in q.bbox.split(",")]
        if len(parts) != 4:
            raise ValueError
        return (parts[0], parts[1], parts[2], parts[3])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox must be 'minLat,minLon,maxLat,maxLon'",
        )


_citizen_only = require_role("citizen")


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    body: ReportCreate,
    current_user: User = Depends(_citizen_only),
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
    bbox = _parse_bbox(q)
    filters = ReportFilters(
        report_type_ids=[q.type_id] if q.type_id else None,
        urgencies=[Urgency(q.urgency)] if q.urgency else None,
        statuses=[ReportStatus(q.status)] if q.status else None,
        author_id=q.author_id,
        since=q.since,
        until=q.until,
        bbox=bbox,
    )
    return ListReportsGeoJSON(report_repo).execute(filters)


def _to_search_result(report: Report, score: float) -> ReportSearchResult:
    return ReportSearchResult(
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
        score=score,
    )


def _to_public_forwarding(forwarding: Forwarding, reports: list[Report]) -> PublicForwardingResponse:
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


# Registered before GET /{id} so FastAPI does not match "/similar-to-set" against "/{id}".
@router.post("/similar-to-set", response_model=list[ReportSearchResult])
def similar_to_set(
    body: ReportSetSimilarRequest,
    _current_user: User = Depends(_agent_or_admin),
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> list[ReportSearchResult]:
    if search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Semantic search unavailable"
        )
    results = FindSimilarToReportSet(report_repo, search_port).execute(body.report_ids, body.n)
    return [_to_search_result(report, score) for report, score in results]


# Registered before GET /{id} so FastAPI does not match "/search" against "/{id}".
@router.get("/search", response_model=list[ReportSearchResult])
def search_reports(
    q: str,
    n: int = 10,
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> list[ReportSearchResult]:
    if not q.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="q must not be empty"
        )
    if search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Semantic search unavailable"
        )
    n = max(1, min(n, 50))
    results = SearchReports(report_repo, search_port).execute(q, n)
    return [_to_search_result(report, score) for report, score in results]


MAX_RESULTS = 500


@router.post("/query", response_model=ReportQueryResponse)
def query_reports(
    body: ReportQueryRequest,
    current_user: User = Depends(get_current_user),
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> ReportQueryResponse:
    bbox = None
    if body.bbox:
        parts = body.bbox.split(",")
        if len(parts) != 4:
            raise HTTPException(status_code=422, detail="bbox must be 'minLat,minLon,maxLat,maxLon'")
        try:
            bbox = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
        except ValueError:
            raise HTTPException(status_code=422, detail="bbox values must be numbers")

    filters = ReportFilters(
        report_type_ids=body.report_type_ids if body.report_type_ids else None,
        urgencies=[Urgency(u) for u in body.urgencies] if body.urgencies else None,
        statuses=[ReportStatus(s) for s in body.statuses] if body.statuses else None,
        author_id=body.author_id,
        since=body.since,
        until=body.until,
        bbox=bbox,
        text=body.text,
    )

    page = QueryReports(report_repo, search_port).execute(
        filters,
        q=body.q,
        limit=body.limit,
        offset=body.offset,
        max_results=MAX_RESULTS,
    )

    items = [
        ReportQueryItem(
            id=r.id,
            text=r.text,
            lat=r.lat,
            lon=r.lon,
            urgency=r.urgency.value,
            status=r.status.value,
            report_type_id=r.report_type_id,
            author_id=r.author_id,
            photo_url=r.photo_url,
            created_at=r.created_at,
            score=score,
        )
        for r, score in page.items
    ]

    return ReportQueryResponse(
        items=items,
        total=page.total,
        limit=page.limit,
        offset=page.offset,
        ranked_by=page.ranked_by,
    )


@router.get("/{id}/similar", response_model=list[ReportSearchResult])
def similar_reports(
    id: str,
    n: int = 5,
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> list[ReportSearchResult]:
    if search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Semantic search unavailable"
        )
    n = max(1, min(n, 50))
    try:
        results = FindSimilarReports(report_repo, search_port).execute(id, n)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [_to_search_result(report, score) for report, score in results]


@router.get("/{id}/forwardings", response_model=list[PublicForwardingResponse])
def list_report_forwardings(
    id: str,
    report_repo: IReportRepository = Depends(get_report_repo),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
) -> list[PublicForwardingResponse]:
    try:
        pairs = ListForwardingsForReport(forwarding_repo, report_repo).execute(id)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [_to_public_forwarding(fwd, reports) for fwd, reports in pairs]


@router.get("/keywords", response_model=KeywordListResponse)
def get_keywords(
    q: ReportFiltersQuery = Depends(),
    min_docs: int = Query(default=3, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    report_repo=Depends(get_report_repo),
    keyword_extractor: ITopicModelPort | None = Depends(get_keyword_extractor),
) -> KeywordListResponse:
    if keyword_extractor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keyword extraction unavailable",
        )
    bbox = _parse_bbox(q)
    filters = ReportFilters(
        report_type_ids=[q.type_id] if q.type_id else None,
        urgencies=[Urgency(q.urgency)] if q.urgency else None,
        statuses=[ReportStatus(q.status)] if q.status else None,
        since=q.since,
        until=q.until,
        bbox=bbox,
    )
    reports = report_repo.find_all(filters)
    raw = GetTopicsForReports(keyword_extractor, min_docs=min_docs).execute(reports)
    items = [KeywordItem(cluster_id=t["topic_id"], terms=t["terms"], count=t["count"]) for t in raw]
    return KeywordListResponse(keywords=items, total_reports=len(reports))


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
