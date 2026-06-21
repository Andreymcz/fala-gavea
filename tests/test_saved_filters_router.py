from __future__ import annotations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_filter(client, headers: dict, name: str = "My Filter", body: dict | None = None) -> dict:
    if body is None:
        body = {"status": "pendente", "urgency": "alta"}
    resp = client.post(
        "/saved-filters/",
        json={"name": name, "body": body},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_unauthenticated_post_returns_401(client):
    resp = client.post("/saved-filters/", json={"name": "x", "body": {}})
    assert resp.status_code == 401


def test_create_returns_201_with_fields(client, citizen_headers):
    data = _create_filter(client, citizen_headers, name="Filter A", body={"status": "pendente"})
    assert "id" in data
    assert data["name"] == "Filter A"
    assert data["body"] == {"status": "pendente"}
    assert data["schema_ver"] == "1"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["deprecated_fields"] == []


def test_list_returns_created_item(client, citizen_headers):
    _create_filter(client, citizen_headers, name="Filter B")
    resp = client.get("/saved-filters/", headers=citizen_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()]
    assert "Filter B" in names


def test_get_returns_200(client, citizen_headers):
    created = _create_filter(client, citizen_headers, name="Filter C")
    resp = client.get(f"/saved-filters/{created['id']}", headers=citizen_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_another_users_filter_returns_404(client, citizen_headers, agent_headers):
    # citizen creates a filter
    created = _create_filter(client, citizen_headers, name="Private")
    # agent tries to get it — should 404 (BOLA prevention)
    resp = client.get(f"/saved-filters/{created['id']}", headers=agent_headers)
    assert resp.status_code == 404


def test_patch_updates_name(client, citizen_headers):
    created = _create_filter(client, citizen_headers, name="Old Name")
    resp = client.patch(
        f"/saved-filters/{created['id']}",
        json={"name": "New Name"},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_returns_204(client, citizen_headers):
    created = _create_filter(client, citizen_headers)
    resp = client.delete(f"/saved-filters/{created['id']}", headers=citizen_headers)
    assert resp.status_code == 204


def test_get_after_delete_returns_404(client, citizen_headers):
    created = _create_filter(client, citizen_headers)
    client.delete(f"/saved-filters/{created['id']}", headers=citizen_headers)
    resp = client.get(f"/saved-filters/{created['id']}", headers=citizen_headers)
    assert resp.status_code == 404
