from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from fala_gavea.application.use_cases.reports.bulk_create_reports import BulkCreateReports
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer
from fala_gavea.presentation.api.dependencies import (
    get_report_indexer,
    get_report_repo,
    get_report_type_repo,
    require_role,
)
from fala_gavea.presentation.schemas.seed_schemas import SeedErrorItem, SeedRelatosResponse

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
