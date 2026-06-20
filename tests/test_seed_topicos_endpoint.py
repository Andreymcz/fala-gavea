"""Integration tests for POST /admin/seed/topicos."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient


def _csv(rows: list[dict], cols: list[str] | None = None) -> bytes:
    if not rows:
        return b""
    c = cols or list(rows[0].keys())
    lines = [",".join(c)]
    for row in rows:
        lines.append(",".join(str(row.get(k, "")) for k in c))
    return "\n".join(lines).encode("utf-8")


def test_seed_topicos_happy_path(client: TestClient, admin_headers: dict) -> None:
    csv_bytes = _csv([
        {"nome": "Iluminacao publica", "descricao": "Luz"},
        {"nome": "Buraco na via", "descricao": ""},
    ])
    resp = client.post(
        "/admin/seed/topicos",
        files={"file": ("topicos.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["inserted"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []


def test_seed_topicos_duplicate_skipped(client: TestClient, admin_headers: dict) -> None:
    csv_bytes = _csv([{"nome": "Iluminacao publica", "descricao": "Luz"}])
    client.post("/admin/seed/topicos", files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")}, headers=admin_headers)
    resp = client.post("/admin/seed/topicos", files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")}, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 0
    assert data["skipped"] == 1


def test_seed_topicos_invalid_name_length(client: TestClient, admin_headers: dict) -> None:
    csv_bytes = _csv([{"nome": "Ok", "descricao": ""}])  # 2 chars, too short
    resp = client.post("/admin/seed/topicos", files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")}, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 0
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1


def test_seed_topicos_non_admin_gets_403(client: TestClient, citizen_headers: dict) -> None:
    csv_bytes = _csv([{"nome": "Tipo valido aqui", "descricao": ""}])
    resp = client.post("/admin/seed/topicos", files={"file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")}, headers=citizen_headers)
    assert resp.status_code == 403
