"""Seed script: advance forwardings through their lifecycle via the REST API.

This is the showcase's "resolved" data: it moves a deterministic subset of
forwardings to `solucao_em_andamento` and `finalizado` via
PATCH /forwardings/{id}/status (agent/admin-only), so the UI shows all three
ForwardingStatus states.

NOTE: "resolution" is modelled at the FORWARDING level. `ReportStatus.resolvido`
exists in the enum but has no API transition — reports reach `encaminhado` when
forwarded and stay there. Marking a report `resolvido` would need a new endpoint
or a direct DB write (the latter violates the API-only seed convention), so it is
out of scope here (see plan-000183 Findings/Suggestions).

Valid ForwardingStatus values: aguardando_solucao, solucao_em_andamento, finalizado.

Idempotent: forwardings already past `aguardando_solucao` are skipped (--force overrides).

Pre-requisites:
    uv run python scripts/seed_users.py
    uv run python scripts/seed_forwardings.py
    API server must be running.

Usage:
    uv run python scripts/seed_forwarding_lifecycle.py [--url URL] [--seed 42] [--force]
"""
from __future__ import annotations

import argparse
import random
import sys

import httpx

AGENT_EMAIL = "agente@gavea.br"
AGENT_PASSWORD = "agente12345"

_INITIAL = "aguardando_solucao"
_IN_PROGRESS = "solucao_em_andamento"
_FINALIZED = "finalizado"


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _fetch_forwardings(client: httpx.Client, token: str) -> list[dict]:
    resp = client.get("/forwardings", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        print(f"Error fetching forwardings ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance forwardings through their lifecycle.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--force", action="store_true", help="Advance even forwardings already past the initial state"
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")
    rng = random.Random(args.seed)

    counts = {_INITIAL: 0, _IN_PROGRESS: 0, _FINALIZED: 0}
    skipped = 0
    errors = 0

    with httpx.Client(base_url=base, timeout=30) as client:
        token = _login(client, AGENT_EMAIL, AGENT_PASSWORD)
        headers = {"Authorization": f"Bearer {token}"}

        forwardings = _fetch_forwardings(client, token)
        candidates = [
            f for f in forwardings if args.force or f.get("status") == _INITIAL
        ]
        skipped = len(forwardings) - len(candidates)
        print(f"Found {len(forwardings)} forwarding(s); {len(candidates)} eligible to advance.")

        # Deterministic split: ~1/3 stay initial, ~1/3 in-progress, ~1/3 finalized.
        rng.shuffle(candidates)
        for idx, fwd in enumerate(candidates):
            bucket = idx % 3
            if bucket == 0:
                counts[_INITIAL] += 1  # leave at aguardando_solucao
                continue
            new_status = _IN_PROGRESS if bucket == 1 else _FINALIZED
            resp = client.patch(
                f"/forwardings/{fwd['id']}/status",
                json={"status": new_status},
                headers=headers,
            )
            if resp.status_code == 200:
                counts[new_status] += 1
            else:
                errors += 1
                print(
                    f"  Error {resp.status_code} advancing {fwd['id']} -> {new_status}: {resp.text}",
                    file=sys.stderr,
                )

    print(
        f"\nDone. Lifecycle distribution among advanced/eligible: "
        f"aguardando_solucao={counts[_INITIAL]}, solucao_em_andamento={counts[_IN_PROGRESS]}, "
        f"finalizado={counts[_FINALIZED]}; skipped (already advanced)={skipped}, errors={errors}"
    )


if __name__ == "__main__":
    main()
