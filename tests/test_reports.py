from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_report_authenticated(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    resp = client.post(
        "/reports/",
        json={
            "text": "Poste apagado na rua principal",
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": sample_report_type,
        },
        headers=citizen_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pendente"
    assert data["urgency"] == "alta"
    assert "id" in data


def test_create_report_unauthenticated(client: TestClient, sample_report_type: str) -> None:
    resp = client.post(
        "/reports/",
        json={
            "text": "Poste apagado na rua principal",
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": sample_report_type,
        },
    )
    assert resp.status_code == 401


def test_create_report_text_too_short(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    resp = client.post(
        "/reports/",
        json={
            "text": "curto",
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": sample_report_type,
        },
        headers=citizen_headers,
    )
    assert resp.status_code == 422


def test_create_report_invalid_report_type(client: TestClient, citizen_headers: dict) -> None:
    resp = client.post(
        "/reports/",
        json={
            "text": "Poste apagado na rua principal",
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": "nonexistent-type-id",
        },
        headers=citizen_headers,
    )
    assert resp.status_code == 422


def test_geojson_returns_feature_collection(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    client.post(
        "/reports/",
        json={
            "text": "Poste apagado na rua principal",
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": sample_report_type,
        },
        headers=citizen_headers,
    )
    resp = client.get("/reports/geojson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feature = data["features"][0]
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [-43.2272, -22.9731]
    # author_id/photo_url are required by the map popup (self-vote guard).
    assert "author_id" in feature["properties"]
    assert "photo_url" in feature["properties"]


def test_geojson_urgency_filter(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    client.post(
        "/reports/",
        json={"text": "Alta urgencia aqui no local", "lat": -22.97, "lon": -43.22, "urgency": "alta", "report_type_id": sample_report_type},
        headers=citizen_headers,
    )
    client.post(
        "/reports/",
        json={"text": "Baixa urgencia nesse ponto", "lat": -22.98, "lon": -43.23, "urgency": "baixa", "report_type_id": sample_report_type},
        headers=citizen_headers,
    )
    resp = client.get("/reports/geojson?urgency=alta")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["features"]) == 1
    assert data["features"][0]["properties"]["urgency"] == "alta"


def test_get_report_authenticated(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    create_resp = client.post(
        "/reports/",
        json={"text": "Poste apagado na rua principal", "lat": -22.97, "lon": -43.22, "urgency": "media", "report_type_id": sample_report_type},
        headers=citizen_headers,
    )
    report_id = create_resp.json()["id"]
    resp = client.get(f"/reports/{report_id}", headers=citizen_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == report_id


def test_get_report_not_found(client: TestClient, citizen_headers: dict) -> None:
    resp = client.get("/reports/nonexistent-id-12345", headers=citizen_headers)
    assert resp.status_code == 404


def test_get_report_unauthenticated(client: TestClient, citizen_headers: dict, sample_report_type: str) -> None:
    create_resp = client.post(
        "/reports/",
        json={"text": "Poste apagado na rua principal", "lat": -22.97, "lon": -43.22, "urgency": "media", "report_type_id": sample_report_type},
        headers=citizen_headers,
    )
    report_id = create_resp.json()["id"]
    resp = client.get(f"/reports/{report_id}")
    assert resp.status_code == 401
