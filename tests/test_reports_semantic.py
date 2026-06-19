from __future__ import annotations

from fastapi.testclient import TestClient

from fala_gavea.presentation.api.dependencies import get_semantic_search_port


class _FakeSearchPort:
    """Fake ISemanticSearchPort returning fixed (id, score) tuples -- no model
    or ChromaDB load."""

    def __init__(self, search_hits=None, similar_hits=None) -> None:
        self._search_hits = search_hits or []
        self._similar_hits = similar_hits or []

    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]:
        return self._search_hits

    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]:
        return self._similar_hits


def _create_report(client: TestClient, headers: dict, report_type_id: str, text: str) -> str:
    resp = client.post(
        "/reports/",
        json={
            "text": text,
            "lat": -22.9731,
            "lon": -43.2272,
            "urgency": "alta",
            "report_type_id": report_type_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_search_returns_results_with_score(
    client: TestClient, citizen_headers: dict, sample_report_type: str
) -> None:
    report_id = _create_report(client, citizen_headers, sample_report_type, "Buraco grande na pista")
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        search_hits=[(report_id, 0.9)]
    )

    resp = client.get("/reports/search?q=buraco")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == report_id
    assert data[0]["score"] == 0.9
    assert data[0]["urgency"] == "alta"


def test_search_empty_q_returns_422(client: TestClient) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort()
    resp = client.get("/reports/search?q=")
    assert resp.status_code == 422


def test_search_missing_q_returns_422(client: TestClient) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort()
    resp = client.get("/reports/search")
    assert resp.status_code == 422


def test_search_unavailable_returns_503(client: TestClient) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: None
    resp = client.get("/reports/search?q=buraco")
    assert resp.status_code == 503


def test_search_is_public(
    client: TestClient, citizen_headers: dict, sample_report_type: str
) -> None:
    report_id = _create_report(client, citizen_headers, sample_report_type, "Iluminacao apagada aqui")
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        search_hits=[(report_id, 0.5)]
    )
    # no auth header -> still 200 (public endpoint)
    resp = client.get("/reports/search?q=luz")
    assert resp.status_code == 200


def test_similar_returns_neighbors(
    client: TestClient, citizen_headers: dict, sample_report_type: str
) -> None:
    base_id = _create_report(client, citizen_headers, sample_report_type, "Relato base sobre buraco")
    other_id = _create_report(client, citizen_headers, sample_report_type, "Outro relato parecido")
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        similar_hits=[(other_id, 0.8)]
    )

    resp = client.get(f"/reports/{base_id}/similar")

    assert resp.status_code == 200
    data = resp.json()
    assert [item["id"] for item in data] == [other_id]
    assert data[0]["score"] == 0.8


def test_similar_base_not_found_404(client: TestClient) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        similar_hits=[]
    )
    resp = client.get("/reports/nonexistent-id-12345/similar")
    assert resp.status_code == 404


def test_similar_unavailable_returns_503(client: TestClient) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: None
    resp = client.get("/reports/some-id/similar")
    assert resp.status_code == 503
