from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fala_gavea.application.use_cases.report_types.create_report_type import CreateReportType
from fala_gavea.domain.entities.report import Report, Urgency
from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.exceptions import InvalidInputError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.password_service import PasswordService

_log = logging.getLogger(__name__)

# Bounding box da Gávea (mesmas constantes de scripts/seed_relatos.py).
_LAT_MIN, _LAT_MAX = -22.975, -22.953
_LON_MIN, _LON_MAX = -43.235, -43.205
_DEFAULT_PASSWORD = "changeme"


@dataclass
class BulkResult:
    inserted: int
    skipped: int
    errors: list[dict] = field(default_factory=list)


class BulkCreateReports:
    def execute(
        self,
        rows: list[dict],
        report_type_repo: IReportTypeRepository,
        report_repo: IReportRepository,
        user_repo: IUserRepository,
        password_service: PasswordService,
        indexer: IReportIndexer | None = None,
    ) -> BulkResult:
        inserted = 0
        skipped = 0
        errors: list[dict] = []
        author_cache: dict[str, str] = {}

        for i, row in enumerate(rows):
            user_id = str(row.get("user_id", "")).strip()
            if not user_id:
                skipped += 1
                errors.append({"row": i, "reason": "user_id obrigatório"})
                continue

            # Resolver/criar autor (deduplicado por e-mail sintético, com cache local).
            if user_id not in author_cache:
                email = f"{user_id}@seed.gavea.br"
                user = user_repo.find_by_email(email)
                if user is None:
                    user = User.create(
                        email=email,
                        password_hash=password_service.hash_password(_DEFAULT_PASSWORD),
                        name=f"Cidadão {user_id}",
                        role=UserRole.citizen,
                    )
                    user_repo.save(user)
                author_cache[user_id] = user.id

            topico = str(row.get("topico", "")).strip()
            if not topico:
                skipped += 1
                errors.append({"row": i, "reason": "topico obrigatório"})
                continue
            rt = report_type_repo.find_by_name(topico)
            if rt is None:
                try:
                    rt = CreateReportType(report_type_repo).execute(topico, None)
                except InvalidInputError:
                    skipped += 1
                    errors.append({"row": i, "reason": f"topico inválido: {topico!r}"})
                    continue

            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except (KeyError, TypeError, ValueError):
                lat = round(random.uniform(_LAT_MIN, _LAT_MAX), 6)
                lon = round(random.uniform(_LON_MIN, _LON_MAX), 6)

            created_at: datetime | None = row.get("data")
            if created_at is not None and not isinstance(created_at, datetime):
                try:
                    parsed = datetime.fromisoformat(str(created_at))
                    created_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
                except ValueError:
                    created_at = None

            raw_urgency = str(row.get("urgency", "")).strip().lower()
            urgency = Urgency(raw_urgency) if raw_urgency in {"alta", "media", "baixa"} else Urgency.media

            text = str(row.get("descricao", "")).strip()
            report = Report.create(
                text=text,
                lat=lat,
                lon=lon,
                urgency=urgency,
                report_type_id=rt.id,
                author_id=author_cache[user_id],
                created_at=created_at,
            )
            report_repo.save(report)
            inserted += 1

            if indexer is not None:
                try:
                    indexer.index(report)
                except Exception as exc:
                    _log.warning("Failed to index report %s: %s", report.id, exc)

        return BulkResult(inserted=inserted, skipped=skipped, errors=errors)
