from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from fala_gavea.presentation.api.dependencies import get_semantic_search_port


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_report(
    client: TestClient,
    headers: dict,
    report_type_id: str,
    text: str = "Poste apagado na rua principal perto da praca",
    lat: float = -22.9731,
    lon: float = -43.2272,
) -> dict:
    resp = client.post(
        "/reports/",
        json={
            "text": text,
            "lat": lat,
            "lon": lon,
            "urgency": "alta",
            "report_type_id": report_type_id,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_forwarding(client: TestClient, agent_headers: dict, report_ids: list[str]) -> dict:
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua",
            "report_ids": report_ids,
        },
        headers=agent_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class _FakeSearchPort:
    """Fake ISemanticSearchPort returning fixed (id, score) tuples for set similarity."""

    def __init__(self, set_hits=None) -> None:
        self._set_hits = set_hits or []

    def search(self, query: str, n: int = 10):
        return []

    def similar(self, report_id: str, n: int = 5):
        return []

    def similar_to_set(self, report_ids: list[str], n: int = 5):
        return self._set_hits

    def rank(self, query: str, ids: list[str]):
        return {}


# ---------------------------------------------------------------------------
# Item 1 — author filter
# ---------------------------------------------------------------------------

def test_author_filter_query_returns_only_author_reports(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    # citizen report
    r_citizen = _create_report(client, citizen_headers, sample_report_type, "Relato do cidadao sobre buraco")
    # agent report
    r_agent = _create_report(client, agent_headers, sample_report_type, "Relato do agente sobre poste")

    citizen_author_id = r_citizen["author_id"]

    resp = client.post(
        "/reports/query",
        json={"author_id": citizen_author_id},
        headers=citizen_headers,
    )
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["items"]]
    assert r_citizen["id"] in ids
    assert r_agent["id"] not in ids


def test_no_author_filter_returns_all(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type, "Relato A do cidadao buraco grande")
    r2 = _create_report(client, agent_headers, sample_report_type, "Relato B do agente poste apagado")

    resp = client.post("/reports/query", json={}, headers=citizen_headers)
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert r1["id"] in ids
    assert r2["id"] in ids


def test_author_filter_geojson(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r_citizen = _create_report(client, citizen_headers, sample_report_type, "Geojson cidadao buraco")
    _create_report(client, agent_headers, sample_report_type, "Geojson agente poste")

    resp = client.get(f"/reports/geojson?author_id={r_citizen['author_id']}")
    assert resp.status_code == 200
    feature_ids = [f["properties"]["id"] for f in resp.json()["features"]]
    assert r_citizen["id"] in feature_ids
    assert len(feature_ids) == 1


# ---------------------------------------------------------------------------
# Item 2 — public forwarding read
# ---------------------------------------------------------------------------

def test_public_forwarding_list_anonymous_no_agent_id(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    # no auth header
    resp = client.get("/forwardings/public")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    ids = [f["id"] for f in data]
    assert fwd["id"] in ids
    for f in data:
        assert "agent_id" not in f


def test_public_forwarding_detail_anonymous_no_agent_id(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.get(f"/forwardings/public/{fwd['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"] == fwd["id"]
    assert "agent_id" not in data
    assert len(data["reports"]) == 1


def test_public_forwarding_status_filter(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.get("/forwardings/public?status=aguardando_solucao")
    assert resp.status_code == 200
    assert fwd["id"] in [f["id"] for f in resp.json()]

    resp2 = client.get("/forwardings/public?status=finalizado")
    assert resp2.status_code == 200
    assert resp2.json() == []


def test_public_forwarding_detail_not_found(client: TestClient) -> None:
    resp = client.get(f"/forwardings/public/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Item 3 — report -> forwardings reverse lookup
# ---------------------------------------------------------------------------

def test_report_forwardings_returns_linked(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    # public, no auth
    resp = client.get(f"/reports/{r1['id']}/forwardings")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert [f["id"] for f in data] == [fwd["id"]]
    assert "agent_id" not in data[0]


def test_report_forwardings_empty_when_none(
    client: TestClient, citizen_headers: dict, sample_report_type: str
) -> None:
    r1 = _create_report(client, citizen_headers, sample_report_type)
    resp = client.get(f"/reports/{r1['id']}/forwardings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_report_forwardings_unknown_report_404(client: TestClient) -> None:
    resp = client.get(f"/reports/{uuid.uuid4()}/forwardings")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Item 4 — set similarity
# ---------------------------------------------------------------------------

def test_similar_to_set_returns_pendente_neighbors(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    seed = _create_report(client, citizen_headers, sample_report_type, "Relato semente buraco")
    neighbor_open = _create_report(client, citizen_headers, sample_report_type, "Vizinho aberto buraco")

    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        set_hits=[(neighbor_open["id"], 0.9)]
    )

    resp = client.post(
        "/reports/similar-to-set",
        json={"report_ids": [seed["id"]], "n": 5},
        headers=agent_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert [item["id"] for item in data] == [neighbor_open["id"]]
    assert data[0]["score"] == 0.9


def test_similar_to_set_filters_non_pendente(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    seed = _create_report(client, citizen_headers, sample_report_type, "Relato semente outro")
    open_one = _create_report(client, citizen_headers, sample_report_type, "Aberto pendente relato")
    forwarded = _create_report(client, citizen_headers, sample_report_type, "Sera encaminhado relato")

    # Forward `forwarded` -> status becomes encaminhado (not pendente)
    _create_forwarding(client, agent_headers, [forwarded["id"]])

    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        set_hits=[(open_one["id"], 0.8), (forwarded["id"], 0.7)]
    )

    resp = client.post(
        "/reports/similar-to-set",
        json={"report_ids": [seed["id"]]},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert open_one["id"] in ids
    assert forwarded["id"] not in ids


def test_similar_to_set_excludes_seed_ids(
    client: TestClient, citizen_headers: dict, agent_headers: dict, sample_report_type: str
) -> None:
    seed = _create_report(client, citizen_headers, sample_report_type, "Relato semente exclude")
    neighbor = _create_report(client, citizen_headers, sample_report_type, "Vizinho exclude relato")

    # Fake returns the seed itself plus a neighbor; seed must be dropped.
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort(
        set_hits=[(seed["id"], 1.0), (neighbor["id"], 0.6)]
    )

    resp = client.post(
        "/reports/similar-to-set",
        json={"report_ids": [seed["id"]]},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert seed["id"] not in ids
    assert neighbor["id"] in ids


def test_similar_to_set_unavailable_returns_503(
    client: TestClient, agent_headers: dict
) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: None
    resp = client.post(
        "/reports/similar-to-set",
        json={"report_ids": ["x"]},
        headers=agent_headers,
    )
    assert resp.status_code == 503


def test_similar_to_set_citizen_forbidden(
    client: TestClient, citizen_headers: dict, sample_report_type: str
) -> None:
    client.app.dependency_overrides[get_semantic_search_port] = lambda: _FakeSearchPort()
    resp = client.post(
        "/reports/similar-to-set",
        json={"report_ids": ["x"]},
        headers=citizen_headers,
    )
    assert resp.status_code == 403
