from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from fala_gavea.application.use_cases.admin.wipe_database import WipeDatabase
from fala_gavea.application.use_cases.report_types.bulk_create_report_types import BulkCreateReportTypes
from fala_gavea.application.use_cases.reports.bulk_create_reports import BulkCreateReports
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer
from fala_gavea.presentation.api.dependencies import (
    get_db,
    get_report_indexer,
    get_report_repo,
    get_report_type_repo,
    require_role,
)
from fala_gavea.presentation.schemas.seed_schemas import (
    SeedErrorItem,
    SeedRelatosResponse,
    SeedTopicosResponse,
    WipedCounts,
    WipeResponse,
)

router = APIRouter()


@router.post("/relatos", response_model=SeedRelatosResponse, status_code=status.HTTP_200_OK)
def seed_relatos(
    file: UploadFile,
    current_user: User = Depends(require_role("admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
    indexer: IReportIndexer | None = Depends(get_report_indexer),
) -> SeedRelatosResponse:
    if file.content_type not in ("text/csv", "application/csv", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a CSV (text/csv)",
        )

    raw = file.file.read()
    text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    rows: list[dict] = []
    for row in reader:
        rows.append({
            "descricao": row.get("texto_relato", ""),
            "lat": row.get("latitude", ""),
            "lon": row.get("longitude", ""),
            "data": row.get("data", ""),
            "topico": row.get("topico", ""),
        })

    result = BulkCreateReports().execute(
        rows,
        author_id=current_user.id,
        report_type_repo=report_type_repo,
        report_repo=report_repo,
        indexer=indexer,
    )

    return SeedRelatosResponse(
        inserted=result.inserted,
        skipped=result.skipped,
        errors=[SeedErrorItem(row=e["row"], reason=e["reason"]) for e in result.errors],
    )


@router.post("/topicos", response_model=SeedTopicosResponse, status_code=status.HTTP_200_OK)
def seed_topicos(
    file: UploadFile,
    current_user: User = Depends(require_role("admin")),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
) -> SeedTopicosResponse:
    if file.content_type not in ("text/csv", "application/csv", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a CSV (text/csv)",
        )

    raw = file.file.read()
    text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    rows = [{"nome": row.get("nome", ""), "descricao": row.get("descricao")} for row in reader]
    result = BulkCreateReportTypes().execute(rows, report_type_repo)

    return SeedTopicosResponse(
        inserted=result.inserted,
        skipped=result.skipped,
        errors=[SeedErrorItem(row=e["row"], reason=e["reason"]) for e in result.errors],
    )


@router.delete("/wipe", response_model=WipeResponse, status_code=status.HTTP_200_OK)
def wipe_database(
    include_report_types: bool = False,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
    indexer: IReportIndexer | None = Depends(get_report_indexer),
) -> WipeResponse:
    result = WipeDatabase().execute(db, include_report_types=include_report_types, indexer=indexer)
    return WipeResponse(
        wiped=WipedCounts(
            reports=result.reports,
            forwardings=result.forwardings,
            report_types=result.report_types,
        )
    )
