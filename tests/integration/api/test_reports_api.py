from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "text": "Precisa de mais iluminação na rua principal",
    "territory_level": "neighborhood",
    "territory_name": "Gávea",
    "author_id": "user-abc",
}


def test_create_report_returns_201(client: TestClient) -> None:
    response = client.post("/reports/", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == VALID_PAYLOAD["text"]
    assert data["territory_level"] == "neighborhood"
    assert "id" in data
    assert "created_at" in data


def test_create_report_empty_text_returns_422(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "text": ""}
    response = client.post("/reports/", json=payload)
    assert response.status_code == 422


def test_create_report_short_text_returns_422(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "text": "Hi"}
    response = client.post("/reports/", json=payload)
    assert response.status_code == 422


def test_get_report_by_id_returns_200(client: TestClient) -> None:
    created = client.post("/reports/", json=VALID_PAYLOAD).json()
    response = client.get(f"/reports/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_report_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/reports/nonexistent-id")
    assert response.status_code == 404


def test_list_reports_returns_200(client: TestClient) -> None:
    client.post("/reports/", json=VALID_PAYLOAD)
    client.post("/reports/", json=VALID_PAYLOAD)
    response = client.get("/reports/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_report_returns_204(client: TestClient) -> None:
    created = client.post("/reports/", json=VALID_PAYLOAD).json()
    response = client.delete(f"/reports/{created['id']}")
    assert response.status_code == 204


def test_delete_report_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/reports/ghost-id")
    assert response.status_code == 404
