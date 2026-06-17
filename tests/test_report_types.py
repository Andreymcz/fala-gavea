from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import (
    SQLAlchemyReportTypeRepository,
)


def _make_rt(name: str = "Iluminacao publica", active: bool = True) -> ReportType:
    return ReportType(
        id=str(uuid.uuid4()),
        name=name,
        description=None,
        active=active,
        created_at=datetime.now(UTC),
    )


# 1. GET /report_types -- no auth -- returns empty list
def test_list_report_types_empty(client):
    resp = client.get("/report_types/")
    assert resp.status_code == 200
    assert resp.json() == []


# 2. GET /report_types -- returns only active types
def test_list_report_types_only_active(client, db_session):
    repo = SQLAlchemyReportTypeRepository(db_session)
    repo.save(_make_rt("Active Type", active=True))
    inactive = _make_rt("Inactive Type", active=False)
    repo.save(inactive)

    resp = client.get("/report_types/")
    assert resp.status_code == 200
    names = [item["name"] for item in resp.json()]
    assert "Active Type" in names
    assert "Inactive Type" not in names


# 3. POST /report_types -- admin -- creates type
def test_create_report_type_admin(client, admin_headers):
    resp = client.post(
        "/report_types/",
        json={"name": "Novo Tipo", "description": "Descricao do novo tipo"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Novo Tipo"
    assert data["active"] is True
    assert "id" in data


# 4. POST /report_types -- non-admin (citizen) -- 403
def test_create_report_type_citizen_forbidden(client, citizen_headers):
    resp = client.post(
        "/report_types/",
        json={"name": "Tipo X"},
        headers=citizen_headers,
    )
    assert resp.status_code == 403


# 5. POST /report_types -- unauthenticated -- 401
def test_create_report_type_unauthenticated(client):
    resp = client.post("/report_types/", json={"name": "Tipo X"})
    assert resp.status_code == 401


# 6. POST /report_types -- invalid name (too short) -- 422
def test_create_report_type_name_too_short(client, admin_headers):
    resp = client.post(
        "/report_types/",
        json={"name": "ab"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


# 7. PATCH /report_types/{id} -- admin -- updates name
def test_update_report_type(client, admin_headers):
    create_resp = client.post(
        "/report_types/",
        json={"name": "Original Name"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    rt_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/report_types/{rt_id}",
        json={"name": "Updated Name"},
        headers=admin_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Name"

    list_resp = client.get("/report_types/")
    names = [item["name"] for item in list_resp.json()]
    assert "Updated Name" in names
    assert "Original Name" not in names


# 8. PATCH /report_types/{id} -- not found -- 404
def test_update_report_type_not_found(client, admin_headers):
    resp = client.patch(
        f"/report_types/{uuid.uuid4()}",
        json={"name": "Does Not Matter"},
        headers=admin_headers,
    )
    assert resp.status_code == 404


# 9. DELETE /report_types/{id} -- admin -- soft-deletes
def test_delete_report_type_soft_delete(client, admin_headers, db_session):
    create_resp = client.post(
        "/report_types/",
        json={"name": "To Be Deleted"},
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    rt_id = create_resp.json()["id"]

    del_resp = client.delete(f"/report_types/{rt_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    list_resp = client.get("/report_types/")
    names = [item["name"] for item in list_resp.json()]
    assert "To Be Deleted" not in names

    repo = SQLAlchemyReportTypeRepository(db_session)
    rt = repo.find_by_id(rt_id)
    assert rt is not None
    assert rt.active is False


# 10. DELETE /report_types/{id} -- not found -- 404
def test_delete_report_type_not_found(client, admin_headers):
    resp = client.delete(f"/report_types/{uuid.uuid4()}", headers=admin_headers)
    assert resp.status_code == 404
