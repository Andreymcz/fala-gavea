"""Integration tests for DELETE /admin/seed/wipe."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository


def _seed_report(db_session, admin_id: str) -> None:
    rt = ReportType(
        id=str(uuid.uuid4()),
        name=f"Tipo {uuid.uuid4()}",
        description=None,
        active=True,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyReportTypeRepository(db_session).save(rt)
    r = Report(
        id=str(uuid.uuid4()),
        text="Texto de relato suficientemente longo para o teste aqui",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.baixa,
        photo_url=None,
        report_type_id=rt.id,
        author_id=admin_id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyReportRepository(db_session).save(r)


def test_wipe_clears_reports(client: TestClient, admin_headers: dict, db_session) -> None:
    # Get admin user id
    resp = client.get("/reports/", headers=admin_headers)  # any authed call to identify user
    # Seed directly via DB
    from sqlalchemy import text
    admin_id = db_session.execute(text("SELECT id FROM users LIMIT 1")).scalar()
    _seed_report(db_session, admin_id)

    resp = client.delete("/admin/seed/wipe", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["wiped"]["reports"] == 1


def test_wipe_with_report_types(client: TestClient, admin_headers: dict, db_session) -> None:
    from sqlalchemy import text
    admin_id = db_session.execute(text("SELECT id FROM users LIMIT 1")).scalar()
    _seed_report(db_session, admin_id)

    resp = client.delete("/admin/seed/wipe?include_report_types=true", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["wiped"]["reports"] == 1
    assert data["wiped"]["report_types"] == 1


def test_wipe_no_data_returns_zeros(client: TestClient, admin_headers: dict) -> None:
    resp = client.delete("/admin/seed/wipe", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["wiped"]["reports"] == 0
    assert data["wiped"]["forwardings"] == 0
    assert data["wiped"]["report_types"] == 0


def test_wipe_non_admin_gets_403(client: TestClient, citizen_headers: dict) -> None:
    resp = client.delete("/admin/seed/wipe", headers=citizen_headers)
    assert resp.status_code == 403
