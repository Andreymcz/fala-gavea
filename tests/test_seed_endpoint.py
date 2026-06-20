"""Integration tests for POST /admin/seed/relatos."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import (
    SQLAlchemyReportTypeRepository,
)
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)


def _csv_bytes(*rows: dict, columns: list[str] | None = None) -> bytes:
    """Build a CSV bytestring from a list of row dicts."""
    if not rows:
        cols = columns or []
    else:
        cols = columns or list(rows[0].keys())
    lines = [",".join(cols)]
    for row in rows:
        lines.append(",".join(str(row.get(c, "")) for c in cols))
    return "\n".join(lines).encode("utf-8")


def test_seed_happy_path(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """3 valid rows (id_cidadao alias) → inserted=3, skipped=0, errors=[]."""
    csv_bytes = _csv_bytes(
        {"id_cidadao": "u1", "texto_relato": "Buraco na calçada perto do parque", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
        {"id_cidadao": "u2", "texto_relato": "Lâmpada queimada na esquina da rua", "latitude": "-22.9740", "longitude": "-43.2280", "data": "2026-01-02", "topico": "Iluminacao publica"},
        {"id_cidadao": "u3", "texto_relato": "Calçada com buraco grande perto da escola", "latitude": "-22.9750", "longitude": "-43.2290", "data": "2026-01-03", "topico": "Iluminacao publica"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["inserted"] == 3
    assert data["skipped"] == 0
    assert data["errors"] == []


def test_seed_new_user_and_topic_are_auto_created(client: TestClient, admin_headers: dict, db_session) -> None:
    """New user_id + nonexistent topico → 200 inserted>=1, synthetic user + ReportType created."""
    csv_bytes = _csv_bytes(
        {"user_id": "novo1", "texto_relato": "Problema de esgoto na rua principal", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Saneamento", "urgency": "alta"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["inserted"] == 1
    assert data["skipped"] == 0

    # Synthetic citizen account created for the new user_id.
    user = SQLAlchemyUserRepository(db_session).find_by_email("novo1@seed.gavea.br")
    assert user is not None
    assert user.name == "Cidadão novo1"
    # Topic auto-created.
    rt = SQLAlchemyReportTypeRepository(db_session).find_by_name("Saneamento")
    assert rt is not None


def test_seed_missing_user_id_is_skipped(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """Row without user_id → skipped with error; user_id is the only required column."""
    csv_bytes = _csv_bytes(
        {"user_id": "", "texto_relato": "Relato sem autor identificado", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["inserted"] == 0
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1
    assert "user_id" in data["errors"][0]["reason"]


def test_seed_missing_coordinates_uses_random_gavea_point(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """Invalid/missing coordinates no longer skip the row — a random Gávea point is generated."""
    csv_bytes = _csv_bytes(
        {"user_id": "u1", "texto_relato": "Problema na rua principal aqui", "latitude": "NOT_A_NUMBER", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["inserted"] == 1
    assert data["skipped"] == 0


def test_seed_non_admin_returns_403(client: TestClient, citizen_headers: dict) -> None:
    """Non-admin caller → 403 Forbidden."""
    csv_bytes = _csv_bytes(
        {"user_id": "u1", "texto_relato": "Algum relato aqui na rua", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=citizen_headers,
    )
    assert resp.status_code == 403
