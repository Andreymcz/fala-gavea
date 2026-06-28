"""Seed script: create test relatos and a forwarding for citizen01@gavea.br.

Creates 10 relatos as citizen01 and 1 forwarding as agente that links
3 of citizen01's relatos plus up to 2 relatos from other users (from the
existing pendente pool), so the forwarding demonstrates cross-user grouping.

Idempotent by default: skips if citizen01 already has forwardings (--force to override).

Pre-requisites:
    uv run python scripts/seed_users.py
    uv run python scripts/seed_relatos.py
    API server must be running.

Usage:
    uv run python scripts/seed_citizen01.py [--url URL] [--force]
"""
from __future__ import annotations

import argparse
import sys

import httpx

_RELATOS: list[dict] = [
    {
        "text": (
            "Poste apagado na esquina da Rua Marques de Sao Vicente com "
            "Rua Padre Leonel Franca — risco para pedestres a noite"
        ),
        "urgency": "alta",
        "type_key": "iluminacao publica",
        "lat": -22.9601,
        "lon": -43.2245,
    },
    {
        "text": (
            "Semaforo com defeito intermitente no cruzamento da Rua Marques de "
            "Sao Vicente com Avenida Borges de Medeiros"
        ),
        "urgency": "alta",
        "type_key": "transito e mobilidade",
        "lat": -22.9635,
        "lon": -43.2198,
    },
    {
        "text": (
            "Calcada destroçada com buracos e raizes expostas impedindo passagem "
            "de cadeirantes na Rua General Garzon"
        ),
        "urgency": "media",
        "type_key": "espaco publico",
        "lat": -22.9654,
        "lon": -43.2217,
    },
    {
        "text": (
            "Acumulo de lixo irregular no terreno proximo ao Parque da Gavea "
            "gerando mau cheiro e atraindo ratos"
        ),
        "urgency": "media",
        "type_key": "lixo e conservacao",
        "lat": -22.9678,
        "lon": -43.2269,
    },
    {
        "text": "Pixacao extensa no muro do clube prejudicando a paisagem urbana na Rua Sao Clemente",
        "urgency": "baixa",
        "type_key": "vandalismo",
        "lat": -22.9556,
        "lon": -43.2136,
    },
    {
        "text": (
            "Buraco profundo no asfalto da Rua Sao Clemente proximo ao numero 200 "
            "causando risco de acidentes para motos e bicicletas"
        ),
        "urgency": "alta",
        "type_key": "espaco publico",
        "lat": -22.9590,
        "lon": -43.2180,
    },
    {
        "text": (
            "Fio eletrico exposto e pendente sobre a calcada na Rua Jardim Botanico "
            "proximo a escola municipal — risco de choque"
        ),
        "urgency": "alta",
        "type_key": "iluminacao publica",
        "lat": -22.9620,
        "lon": -43.2230,
    },
    {
        "text": (
            "Ponto de onibus sem cobertura e com banco danificado na Avenida Epitacio "
            "Pessoa altura do numero 1500"
        ),
        "urgency": "media",
        "type_key": "transito e mobilidade",
        "lat": -22.9648,
        "lon": -43.2155,
    },
    {
        "text": (
            "Arvore com galhos grandes sobre a fiacao eletrica na Rua Visconde de Caravelas "
            "— risco de queda em dia de vento"
        ),
        "urgency": "media",
        "type_key": "espaco publico",
        "lat": -22.9665,
        "lon": -43.2290,
    },
    {
        "text": (
            "Lixo acumulado ha mais de uma semana no container da Rua Marques de "
            "Sao Vicente 450 sem coleta regular"
        ),
        "urgency": "baixa",
        "type_key": "lixo e conservacao",
        "lat": -22.9612,
        "lon": -43.2205,
    },
]

# First 3 of citizen01's relatos go into forwarding A (indices 0-2);
# indices 3-4 go into forwarding B (finalized); indices 5-9 stay pendente.
_CITIZEN01_FORWARDING_SLICE = 3
_FWD_B_START = 3
_FWD_B_END = 5  # created_ids[3:5] -> forwarding B

# Deterministic forwarding states for the citizen-progress journey.
_IN_PROGRESS = "solucao_em_andamento"
_FINALIZED = "finalizado"

# Agent comments that make the "company progress" readable to the citizen.
_PROGRESS_COMMENT = (
    "Equipe RioLuz esteve em campo em 24/06; vistoria concluida, troca das "
    "lampadas programada para o proximo ciclo de manutencao."
)
_CONCLUSION_COMMENT = (
    "Servico concluido: lampadas substituidas e rede testada em campo. "
    "Encaminhamento finalizado."
)


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if resp.status_code != 200:
        print(f"Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _fetch_report_types(client: httpx.Client) -> dict[str, str]:
    resp = client.get("/report_types")
    if resp.status_code != 200:
        print(f"Could not fetch report_types ({resp.status_code})", file=sys.stderr)
        sys.exit(1)
    return {rt["name"].lower().strip(): rt["id"] for rt in resp.json()}


def _fetch_other_pendente_reports(
    client: httpx.Client, token: str, citizen01_ids: set[str], limit: int = 2
) -> list[str]:
    """Return up to `limit` pendente report IDs not authored by citizen01."""
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/reports/query",
        json={"statuses": ["pendente"], "limit": 50, "offset": 0},
        headers=headers,
    )
    if resp.status_code != 200:
        print(
            f"Warning: could not query pendente reports ({resp.status_code}); "
            "forwarding will use only citizen01 relatos.",
            file=sys.stderr,
        )
        return []
    items = resp.json().get("items", [])
    others = [r["id"] for r in items if r["id"] not in citizen01_ids]
    return others[:limit]


def _create_forwarding(
    client: httpx.Client,
    headers: dict[str, str],
    institution: str,
    proposed_solution: str,
    report_ids: list[str],
) -> str:
    """Create a forwarding as the agent and return its id (exits on error)."""
    payload = {
        "institution": institution,
        "proposed_solution": proposed_solution,
        "report_ids": report_ids,
    }
    resp = client.post("/forwardings", json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        print(f"Error creating forwarding ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["id"]


def _set_forwarding_status(
    client: httpx.Client, headers: dict[str, str], forwarding_id: str, new_status: str
) -> None:
    """PATCH a forwarding to a new lifecycle status (exits on error)."""
    resp = client.patch(
        f"/forwardings/{forwarding_id}/status",
        json={"status": new_status},
        headers=headers,
    )
    if resp.status_code != 200:
        print(
            f"Error setting forwarding {forwarding_id} -> {new_status} "
            f"({resp.status_code}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)


def _add_forwarding_comment(
    client: httpx.Client, headers: dict[str, str], forwarding_id: str, text: str
) -> None:
    """POST an agent comment on a forwarding (exits on error)."""
    resp = client.post(
        f"/forwardings/{forwarding_id}/comments",
        json={"text": text},
        headers=headers,
    )
    if resp.status_code not in (200, 201):
        print(
            f"Error commenting on forwarding {forwarding_id} "
            f"({resp.status_code}): {resp.text}",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed citizen01 test relatos and a mixed-user forwarding."
    )
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip idempotency guard and re-seed even if citizen01 already has forwardings",
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")

    with httpx.Client(base_url=base, timeout=30) as client:
        # --- Idempotency guard ---
        citizen01_token = _login(client, "citizen01@gavea.br", "citizen01pass")

        if not args.force:
            resp = client.get(
                "/forwardings/mine",
                headers={"Authorization": f"Bearer {citizen01_token}"},
            )
            if resp.status_code == 200 and len(resp.json()) > 0:
                print(
                    "citizen01 already has forwardings — skipping (use --force to re-seed)."
                )
                return

        # --- Fetch report types ---
        type_map = _fetch_report_types(client)
        fallback_type_id = next(iter(type_map.values())) if type_map else None

        # --- Create 10 relatos as citizen01 ---
        print("Creating relatos as citizen01@gavea.br...")
        created_ids: list[str] = []
        headers_citizen = {"Authorization": f"Bearer {citizen01_token}"}

        for i, r in enumerate(_RELATOS, start=1):
            type_id = type_map.get(r["type_key"], fallback_type_id)
            payload = {
                "text": r["text"],
                "urgency": r["urgency"],
                "report_type_id": type_id,
                "lat": r["lat"],
                "lon": r["lon"],
            }
            resp = client.post("/reports", json=payload, headers=headers_citizen)
            if resp.status_code not in (200, 201):
                print(
                    f"  Error creating relato {i} ({resp.status_code}): {resp.text}",
                    file=sys.stderr,
                )
                sys.exit(1)
            rid = resp.json()["id"]
            created_ids.append(rid)
            print(f"  [{i:02d}] OK  id={rid}  urgency={r['urgency']}  type={r['type_key']}")

        # --- Fetch some pendente reports from other users ---
        print("\nFetching pendente reports from other users for mixed forwarding...")
        agente_token = _login(client, "agente@gavea.br", "agente12345")
        headers_agente = {"Authorization": f"Bearer {agente_token}"}

        other_ids = _fetch_other_pendente_reports(
            client, agente_token, set(created_ids), limit=2
        )
        if other_ids:
            print(f"  Found {len(other_ids)} report(s) from other users: {other_ids}")
        else:
            print("  No other-user pendente reports found; forwarding will be citizen01-only.")

        # --- Forwarding A: citizen01 relatos [0-2] + up to 2 others, IN PROGRESS ---
        # Demonstrates the citizen-progress journey: the responsible org is working
        # on it (solucao_em_andamento) and left a concrete progress comment.
        forwarding_ids = created_ids[:_CITIZEN01_FORWARDING_SLICE] + other_ids
        print(f"\nCreating forwarding A as agente@gavea.br ({len(forwarding_ids)} reports)...")
        fwd_a_id = _create_forwarding(
            client,
            headers_agente,
            institution="CET-Rio / RioLuz",
            proposed_solution=(
                "Encaminhamento de teste para verificacao das funcionalidades de "
                "transparencia cidada. Inclui relatos de citizen01 e de outros usuarios "
                "para demonstrar agrupamento multi-cidadao. "
                "Vistoria e reparo programados para o proximo ciclo de manutencao."
            ),
            report_ids=forwarding_ids,
        )
        print(f"  Forwarding A created: id={fwd_a_id}")
        _set_forwarding_status(client, headers_agente, fwd_a_id, _IN_PROGRESS)
        _add_forwarding_comment(client, headers_agente, fwd_a_id, _PROGRESS_COMMENT)
        print(f"  Forwarding A -> {_IN_PROGRESS} (+ progress comment)")

        # --- Forwarding B: citizen01 relatos [3-4], FINALIZED (resolved contrast) ---
        fwd_b_report_ids = created_ids[_FWD_B_START:_FWD_B_END]
        print(f"\nCreating forwarding B as agente@gavea.br ({len(fwd_b_report_ids)} reports)...")
        fwd_b_id = _create_forwarding(
            client,
            headers_agente,
            institution="RioLuz",
            proposed_solution=(
                "Encaminhamento de troca de lampadas dos relatos de iluminacao de "
                "citizen01. Servico executado e validado em campo."
            ),
            report_ids=fwd_b_report_ids,
        )
        print(f"  Forwarding B created: id={fwd_b_id}")
        _set_forwarding_status(client, headers_agente, fwd_b_id, _FINALIZED)
        _add_forwarding_comment(client, headers_agente, fwd_b_id, _CONCLUSION_COMMENT)
        print(f"  Forwarding B -> {_FINALIZED} (+ conclusion comment)")

        # citizen01 relatos [5-9] are intentionally left without a forwarding
        # (they stay `pendente`) so "meus relatos nao resolvidos" has a mix.
        pendentes = created_ids[_FWD_B_END:]
        print(f"\nLeaving {len(pendentes)} citizen01 relatos as pendente (indices 5-9).")

    # --- Summary ---
    print(
        f"""
citizen01 test data seeded.

  Relatos created : {len(created_ids)} (as citizen01@gavea.br)
  Other reports   : {len(other_ids)} (from other users, included in forwarding A)
  Forwarding A    : id={fwd_a_id}, institution=CET-Rio / RioLuz, status={_IN_PROGRESS}
    Linked reports: {len(forwarding_ids)}
      - citizen01 relatos [0-2]: {created_ids[:_CITIZEN01_FORWARDING_SLICE]}
      - other-user reports     : {other_ids}
    Agent comment   : progress (company working on it)
  Forwarding B    : id={fwd_b_id}, institution=RioLuz, status={_FINALIZED}
    Linked reports: {len(fwd_b_report_ids)}
      - citizen01 relatos [3-4]: {fwd_b_report_ids}
    Agent comment   : conclusion (service finished)
  Pendentes       : {len(pendentes)} (citizen01 relatos [5-9], no forwarding)

  -> "Meus relatos nao resolvidos" mix: {len(created_ids[:_CITIZEN01_FORWARDING_SLICE]) + len(pendentes)} unresolved
     ({len(pendentes)} pendente + {len(created_ids[:_CITIZEN01_FORWARDING_SLICE])} em andamento) / 2 finalized.

To verify in the app:
  1. Login as citizen01@gavea.br / citizen01pass
  2. Go to / (workspace) -> toggle "Meus relatos" in FilterPanel
     Expected: {len(created_ids)} relatos by citizen01 appear in table/map
  3. Go to /encaminhamentos -> check "Meus encaminhamentos"
     Expected: forwarding A (CET-Rio / RioLuz, em andamento, with agent comment) and
               forwarding B (RioLuz, finalizado, with conclusion comment).
     Read the org's progress in A's comment thread.
"""
    )


if __name__ == "__main__":
    main()
