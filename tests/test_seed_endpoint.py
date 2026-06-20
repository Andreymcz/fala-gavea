"""Integration tests for POST /admin/seed/relatos."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient


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


_VALID_COLUMNS = ["id_cidadao", "texto_relato", "latitude", "longitude", "data", "topico"]


def test_seed_happy_path(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """3 valid rows → inserted=3, skipped=0, errors=[]."""
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


def test_seed_unknown_topico(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """One row with invalid topic → skipped=1, errors contains that row's reason."""
    csv_bytes = _csv_bytes(
        {"id_cidadao": "u1", "texto_relato": "Problema de esgoto na rua", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "TopicoInexistente"},
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
    assert "TopicoInexistente" in data["errors"][0]["reason"]


def test_seed_malformed_csv_bad_coordinates(client: TestClient, admin_headers: dict, sample_report_type: str) -> None:
    """Row with non-numeric coordinates → skipped with error, not a server crash."""
    csv_bytes = _csv_bytes(
        {"id_cidadao": "u1", "texto_relato": "Problema na rua principal aqui", "latitude": "NOT_A_NUMBER", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
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


def test_seed_missing_required_columns_returns_200_all_skipped(client: TestClient, admin_headers: dict) -> None:
    """CSV missing all expected columns → all rows skipped (empty topico → unknown type)."""
    # A CSV with only 'comment' column — no texto_relato, no topico, no coordinates
    csv_bytes = b"comment\nsome comment here"
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    # The router maps missing columns to empty strings; empty topico won't match any ReportType
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Row is skipped because topico='' is not found, then coordinates fail
    assert data["inserted"] == 0
    assert data["skipped"] == 1


def test_seed_non_admin_returns_403(client: TestClient, citizen_headers: dict) -> None:
    """Non-admin caller → 403 Forbidden."""
    csv_bytes = _csv_bytes(
        {"id_cidadao": "u1", "texto_relato": "Algum relato aqui na rua", "latitude": "-22.9731", "longitude": "-43.2272", "data": "2026-01-01", "topico": "Iluminacao publica"},
    )
    resp = client.post(
        "/admin/seed/relatos",
        files={"file": ("relatos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=citizen_headers,
    )
    assert resp.status_code == 403
