from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_report(client, headers: dict, report_type_id: str, text: str = "Poste apagado na rua principal perto da praca") -> dict:
    """Create a report via POST /reports and return response JSON."""
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
    return resp.json()


def _create_forwarding(client, agent_headers: dict, report_ids: list[str]) -> dict:
    """Create a forwarding and return response JSON."""
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# 1. Create forwarding with 2 reports — happy path
def test_create_forwarding_success(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type, "Poste apagado na rua A entre cruzamento e esquina")
    r2 = _create_report(client, citizen_headers, sample_report_type, "Poste sem iluminacao na rua A proximo ao numero 100")

    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua conforme solicitacao",
            "report_ids": [r1["id"], r2["id"]],
        },
        headers=agent_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["institution"] == "RioLuz"
    assert data["status"] == "aguardando_solucao"
    assert len(data["reports"]) == 2

    # Verify report statuses changed to encaminhado
    for report_id in [r1["id"], r2["id"]]:
        get_resp = client.get(f"/reports/{report_id}", headers=citizen_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "encaminhado"


# 2. Create forwarding with nonexistent report — 422
def test_create_forwarding_report_not_found(client, agent_headers):
    fake_id = str(uuid.uuid4())
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua",
            "report_ids": [fake_id],
        },
        headers=agent_headers,
    )
    assert resp.status_code == 422


# 3. Create forwarding with empty report_ids — 422
def test_create_forwarding_empty_report_ids(client, agent_headers):
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua",
            "report_ids": [],
        },
        headers=agent_headers,
    )
    assert resp.status_code == 422


# 4. Create forwarding with institution too short — 422
def test_create_forwarding_institution_too_short(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "ab",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua",
            "report_ids": [r1["id"]],
        },
        headers=agent_headers,
    )
    assert resp.status_code == 422


# 5. Create forwarding with proposed_solution too short — 422
def test_create_forwarding_solution_too_short(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Curta demais",
            "report_ids": [r1["id"]],
        },
        headers=agent_headers,
    )
    assert resp.status_code == 422


# 6. Create forwarding as citizen — 403
def test_create_forwarding_citizen_forbidden(client, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    resp = client.post(
        "/forwardings/",
        json={
            "institution": "RioLuz",
            "proposed_solution": "Substituir lampadas queimadas em toda a extensao da rua",
            "report_ids": [r1["id"]],
        },
        headers=citizen_headers,
    )
    assert resp.status_code == 403


# 7. List forwardings — forwarding appears in list
def test_list_forwardings(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.get("/forwardings/", headers=agent_headers)
    assert resp.status_code == 200
    ids = [f["id"] for f in resp.json()]
    assert fwd["id"] in ids


# 8. List forwardings — filter by status
def test_list_forwardings_filter_by_status(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    # Filter matching status — should appear
    resp = client.get("/forwardings/?status=aguardando_solucao", headers=agent_headers)
    assert resp.status_code == 200
    ids = [f["id"] for f in resp.json()]
    assert fwd["id"] in ids

    # Filter non-matching status — should be empty
    resp2 = client.get("/forwardings/?status=finalizado", headers=agent_headers)
    assert resp2.status_code == 200
    assert resp2.json() == []


# 9. Get forwarding detail — includes linked reports
def test_get_forwarding_with_reports(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.get(f"/forwardings/{fwd['id']}", headers=agent_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == fwd["id"]
    assert len(data["reports"]) == 1
    assert data["reports"][0]["id"] == r1["id"]


# 10. Get nonexistent forwarding — 404
def test_get_forwarding_not_found(client, agent_headers):
    fake_id = str(uuid.uuid4())
    resp = client.get(f"/forwardings/{fake_id}", headers=agent_headers)
    assert resp.status_code == 404


# 11. Update forwarding status — success
def test_update_forwarding_status(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.patch(
        f"/forwardings/{fwd['id']}/status",
        json={"status": "solucao_em_andamento"},
        headers=agent_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "solucao_em_andamento"


# 12. Update forwarding status with invalid value — 422
def test_update_forwarding_status_invalid(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.patch(
        f"/forwardings/{fwd['id']}/status",
        json={"status": "xyz"},
        headers=agent_headers,
    )
    assert resp.status_code == 422


# 13. Update forwarding institution — success
def test_update_forwarding_institution(client, agent_headers, citizen_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    fwd = _create_forwarding(client, agent_headers, [r1["id"]])

    resp = client.patch(
        f"/forwardings/{fwd['id']}",
        json={"institution": "COMLURB"},
        headers=agent_headers,
    )
    assert resp.status_code == 200

    get_resp = client.get(f"/forwardings/{fwd['id']}", headers=agent_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["institution"] == "COMLURB"
