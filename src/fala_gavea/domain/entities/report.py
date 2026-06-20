from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class Urgency(str, Enum):
    alta = "alta"
    media = "media"
    baixa = "baixa"


class ReportStatus(str, Enum):
    pendente = "pendente"
    em_analise = "em_analise"
    encaminhado = "encaminhado"
    resolvido = "resolvido"


@dataclass
class Report:
    id: str
    text: str
    lat: float
    lon: float
    urgency: Urgency
    photo_url: str | None
    report_type_id: str
    author_id: str
    status: ReportStatus
    created_at: datetime

    @staticmethod
    def create(
        text: str,
        lat: float,
        lon: float,
        urgency: Urgency,
        report_type_id: str,
        author_id: str,
        photo_url: str | None = None,
        created_at: datetime | None = None,
    ) -> Report:
        return Report(
            id=str(uuid.uuid4()),
            text=text,
            lat=lat,
            lon=lon,
            urgency=urgency,
            photo_url=photo_url,
            report_type_id=report_type_id,
            author_id=author_id,
            status=ReportStatus.pendente,
            created_at=created_at if created_at is not None else datetime.now(UTC),
        )
