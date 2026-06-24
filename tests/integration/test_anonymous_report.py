from __future__ import annotations


def test_anonymous_report_creation_returns_claim_token(client, sample_report_type):
    resp = client.post(
        "/reports",
        json={
            "text": "Buraco na calcada proxima ao posto",
            "lat": -22.9711,
            "lon": -43.2112,
            "urgency": "alta",
            "report_type_id": sample_report_type,
            "anonymous": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["anonymous_claim_token"] is not None
    assert data["author_id"] is None


def test_anonymous_report_returns_coarsened_coords(client, sample_report_type):
    resp = client.post(
        "/reports",
        json={
            "text": "Semaforo quebrado na esquina da rua",
            "lat": -22.97123,
            "lon": -43.21456,
            "urgency": "media",
            "report_type_id": sample_report_type,
            "anonymous": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    # Coords should be rounded to 3 decimal places
    assert data["lat"] == round(-22.97123, 3)
    assert data["lon"] == round(-43.21456, 3)


def test_authenticated_report_returns_no_claim_token(client, citizen_headers, sample_report_type):
    resp = client.post(
        "/reports",
        headers=citizen_headers,
        json={
            "text": "Lixo acumulado na calcada do parque",
            "lat": -22.972,
            "lon": -43.212,
            "urgency": "baixa",
            "report_type_id": sample_report_type,
            "anonymous": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["anonymous_claim_token"] is None
    assert data["author_id"] is not None


def test_non_anonymous_without_auth_returns_401(client, sample_report_type):
    resp = client.post(
        "/reports",
        json={
            "text": "Problema de iluminacao na rua",
            "lat": -22.972,
            "lon": -43.212,
            "urgency": "media",
            "report_type_id": sample_report_type,
            "anonymous": False,
        },
    )
    assert resp.status_code == 401


def test_get_mine_returns_reports_for_valid_token(client, sample_report_type):
    # Create anonymous report
    resp = client.post(
        "/reports",
        json={
            "text": "Calcada com buraco perigoso perto do colegio",
            "lat": -22.9714,
            "lon": -43.2118,
            "urgency": "alta",
            "report_type_id": sample_report_type,
            "anonymous": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    claim_token = data["anonymous_claim_token"]
    report_id = data["id"]

    # Look up by token
    resp2 = client.get(f"/reports/mine?anonymous_token={claim_token}")
    assert resp2.status_code == 200
    results = resp2.json()
    assert any(r["id"] == report_id for r in results)


def test_get_mine_unknown_token_returns_empty(client):
    resp = client.get("/reports/mine?anonymous_token=unknowntokenthatdoesnotexist")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_mine_coarsens_coords(client, sample_report_type):
    resp = client.post(
        "/reports",
        json={
            "text": "Poste de luz com fio exposto na calcada",
            "lat": -22.97178,
            "lon": -43.21891,
            "urgency": "alta",
            "report_type_id": sample_report_type,
            "anonymous": True,
        },
    )
    assert resp.status_code == 201
    claim_token = resp.json()["anonymous_claim_token"]

    resp2 = client.get(f"/reports/mine?anonymous_token={claim_token}")
    assert resp2.status_code == 200
    results = resp2.json()
    assert len(results) == 1
    r = results[0]
    assert r["lat"] == round(-22.97178, 3)
    assert r["lon"] == round(-43.21891, 3)
