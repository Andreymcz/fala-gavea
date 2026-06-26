"""Seed script: add citizen/agent comments to forwardings via the REST API.

Comments on forwardings have no seed today. This also gives the forwarding
comment-synthesis feature (plan-000179) real input to summarize.

Idempotent: a forwarding that already has comments is skipped (unless --force).

Pre-requisites:
    uv run python scripts/seed_users.py
    uv run python scripts/seed_forwardings.py
    API server must be running.

Usage:
    uv run python scripts/seed_comments.py [--url URL] [--seed 42] [--force]
                                           [--max-forwardings 6]
"""
from __future__ import annotations

import argparse
import random
import sys

import httpx

# Commenters: citizens + agent (admin omitted to keep comments citizen-voiced).
COMMENTERS: list[tuple[str, str]] = [
    ("citizen01@gavea.br", "citizen01pass"),
    ("citizen02@gavea.br", "citizen02pass"),
    ("citizen03@gavea.br", "citizen03pass"),
    ("citizen04@gavea.br", "citizen04pass"),
    ("citizen05@gavea.br", "citizen05pass"),
    ("agente@gavea.br", "agente12345"),
]

# Small curated bank of realistic pt-BR comments.
_COMMENTS: list[str] = [
    "Alguma previsão de prazo para a solução?",
    "Mesma situação acontece na minha rua, obrigado por encaminhar.",
    "A equipe esteve no local hoje pela manhã, parece que começaram o reparo.",
    "Continua sem resposta do órgão responsável, já faz duas semanas.",
    "Excelente iniciativa, isso melhora muito a segurança no bairro.",
    "Poderiam priorizar este caso? O risco para pedestres é alto.",
    "Recebi retorno da subprefeitura, vão avaliar na próxima vistoria.",
    "Problema resolvido parcialmente, mas ainda falta a sinalização.",
]


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"  Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _fetch_forwardings(client: httpx.Client, token: str) -> list[str]:
    resp = client.get("/forwardings", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        print(f"Error fetching forwardings ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return [f["id"] for f in resp.json()]


def _existing_comment_count(client: httpx.Client, token: str, forwarding_id: str) -> int:
    resp = client.get(
        f"/forwardings/{forwarding_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        return 0
    return len(resp.json())


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed comments on forwardings.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument(
        "--max-forwardings", type=int, default=6, help="Number of forwardings to comment on"
    )
    parser.add_argument(
        "--force", action="store_true", help="Comment even if the forwarding already has comments"
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")
    rng = random.Random(args.seed)

    created = 0
    skipped = 0

    with httpx.Client(base_url=base, timeout=30) as client:
        tokens = {email: _login(client, email, password) for email, password in COMMENTERS}
        print(f"Logged in {len(tokens)} commenter(s).")

        any_token = next(iter(tokens.values()))
        # GET /forwardings is agent/admin-only — list with the agent token, not a
        # citizen's, or it 403s and the whole comment seed aborts.
        agent_token = tokens.get("agente@gavea.br", any_token)
        forwarding_ids = _fetch_forwardings(client, agent_token)[: args.max_forwardings]
        print(f"Commenting on up to {len(forwarding_ids)} forwarding(s).")

        commenter_emails = list(tokens.keys())

        for fid in forwarding_ids:
            if not args.force and _existing_comment_count(client, any_token, fid) > 0:
                print(f"  Skipped (already has comments): forwarding {fid}")
                skipped += 1
                continue

            n_comments = rng.randint(1, 3)
            chosen_texts = rng.sample(_COMMENTS, k=min(n_comments, len(_COMMENTS)))
            for text in chosen_texts:
                email = rng.choice(commenter_emails)
                resp = client.post(
                    f"/forwardings/{fid}/comments",
                    json={"text": text},
                    headers={"Authorization": f"Bearer {tokens[email]}"},
                )
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    print(
                        f"  Error {resp.status_code} commenting on {fid}: {resp.text}",
                        file=sys.stderr,
                    )
            print(f"  Forwarding {fid}: +{len(chosen_texts)} comment(s)")

    print(f"\nDone. Comments created: {created}, forwardings skipped: {skipped}")


if __name__ == "__main__":
    main()
