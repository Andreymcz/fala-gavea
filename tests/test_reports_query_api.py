from __future__ import annotations



def _create_report(client, headers, sample_report_type, urgency="alta", status="pendente"):
    resp = client.post(
        "/reports/",
        json={
            "text": "Problema de iluminacao publica na rua principal",
            "lat": -22.97,
            "lon": -43.23,
            "urgency": urgency,
            "report_type_id": sample_report_type,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_query_filter_urgency(client, citizen_headers, sample_report_type):
    _create_report(client, citizen_headers, sample_report_type, urgency="alta")
    _create_report(client, citizen_headers, sample_report_type, urgency="media")
    _create_report(client, citizen_headers, sample_report_type, urgency="baixa")

    resp = client.post(
        "/reports/query",
        json={"urgencies": ["alta", "media"]},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "ranked_by" in data
    urgencies = {item["urgency"] for item in data["items"]}
    assert urgencies <= {"alta", "media"}
    assert "baixa" not in urgencies


def test_query_bad_urgency_enum(client, citizen_headers):
    resp = client.post(
        "/reports/query",
        json={"urgencies": ["altissima"]},
        headers=citizen_headers,
    )
    assert resp.status_code == 422


def test_query_unauthenticated(client):
    resp = client.post("/reports/query", json={})
    assert resp.status_code == 401


def test_query_pagination_envelope(client, citizen_headers, sample_report_type):
    for _ in range(3):
        _create_report(client, citizen_headers, sample_report_type)

    resp = client.post(
        "/reports/query",
        json={"limit": 2, "offset": 0},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert "total" in data
    assert "ranked_by" in data
    assert len(data["items"]) <= 2


def test_query_empty_filters_returns_all(client, citizen_headers, sample_report_type):
    _create_report(client, citizen_headers, sample_report_type)
    _create_report(client, citizen_headers, sample_report_type)

    resp = client.post(
        "/reports/query",
        json={},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


def test_query_no_q_returns_recency(client, citizen_headers, sample_report_type):
    _create_report(client, citizen_headers, sample_report_type)

    resp = client.post(
        "/reports/query",
        json={},
        headers=citizen_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["ranked_by"] == "recency"
