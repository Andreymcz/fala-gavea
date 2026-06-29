from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from fala_gavea.application.use_cases.admin.wipe_database import WipeDatabase
from fala_gavea.application.use_cases.report_types.bulk_create_report_types import BulkCreateReportTypes
from fala_gavea.application.use_cases.reports.bulk_create_reports import BulkCreateReports
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.presentation.api.dependencies import (
    get_db,
    get_password_service,
    get_report_indexer,
    get_report_repo,
    get_report_type_repo,
    get_user_repo,
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

_CSV_CONTENT_TYPES = ("text/csv", "application/csv", "application/octet-stream")


def _require_csv(file: UploadFile) -> None:
    if file.content_type not in _CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a CSV (text/csv)",
        )


def _parse_relatos_rows(file: UploadFile) -> list[dict]:
    raw = file.file.read()
    text = raw.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [
        {
            "user_id": row.get("user_id", "") or row.get("id_cidadao", ""),
            "descricao": row.get("texto_relato", ""),
            "lat": row.get("latitude", ""),
            "lon": row.get("longitude", ""),
            "data": row.get("data", ""),
            "topico": row.get("topico", ""),
            "urgency": row.get("urgency", ""),
        }
        for row in reader
    ]


@router.post("/relatos", response_model=SeedRelatosResponse, status_code=status.HTTP_200_OK)
def seed_relatos(
    file: UploadFile,
    current_user: User = Depends(require_role("admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
    user_repo: IUserRepository = Depends(get_user_repo),
    password_service: PasswordService = Depends(get_password_service),
    indexer: IReportIndexer | None = Depends(get_report_indexer),
) -> SeedRelatosResponse:
    _require_csv(file)
    rows = _parse_relatos_rows(file)

    result = BulkCreateReports().execute(
        rows,
        report_type_repo=report_type_repo,
        report_repo=report_repo,
        user_repo=user_repo,
        password_service=password_service,
        indexer=indexer,
    )

    return SeedRelatosResponse(
        inserted=result.inserted,
        skipped=result.skipped,
        errors=[SeedErrorItem(row=e["row"], reason=e["reason"]) for e in result.errors],
    )


@router.post("/relatos/stream")
def seed_relatos_stream(
    file: UploadFile,
    current_user: User = Depends(require_role("admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    report_type_repo: IReportTypeRepository = Depends(get_report_type_repo),
    user_repo: IUserRepository = Depends(get_user_repo),
    password_service: PasswordService = Depends(get_password_service),
    indexer: IReportIndexer | None = Depends(get_report_indexer),
) -> StreamingResponse:
    """Same as ``/relatos`` but streams NDJSON progress so the UI can show a bar.

    Emits one JSON object per line:
      - ``{"type": "progress", "processed", "total", "inserted", "skipped"}``
      - ``{"type": "done", "inserted", "skipped", "errors": [...]}`` (terminal)
      - ``{"type": "error", "detail"}`` if processing raises mid-stream
    The HTTP status is 200 as soon as the stream opens, so validation errors
    (e.g. non-CSV) are still raised up-front before streaming starts.
    """
    _require_csv(file)
    rows = _parse_relatos_rows(file)

    def event_stream() -> Iterator[str]:
        gen = BulkCreateReports().execute_iter(
            rows,
            report_type_repo,
            report_repo,
            user_repo,
            password_service,
            indexer,
        )
        try:
            while True:
                try:
                    progress = next(gen)
                except StopIteration as stop:
                    result = stop.value
                    yield json.dumps(
                        {
                            "type": "done",
                            "inserted": result.inserted,
                            "skipped": result.skipped,
                            "errors": result.errors,
                        }
                    ) + "\n"
                    return
                yield json.dumps(
                    {
                        "type": "progress",
                        "processed": progress.processed,
                        "total": progress.total,
                        "inserted": progress.inserted,
                        "skipped": progress.skipped,
                    }
                ) + "\n"
        except Exception as exc:  # noqa: BLE001 — surface failure as a stream event
            yield json.dumps({"type": "error", "detail": str(exc)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


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
