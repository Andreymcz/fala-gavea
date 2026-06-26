"""Seed script: create named saved filters per user via the REST API.

Saved filters have no seed today, so the saved-filter UI is empty on first login.
This seeds a few useful presets for each non-admin user. The filter `body` mirrors
the report-query shape (report_type_ids, urgencies, statuses, q, limit, offset —
see src/fala_gavea/presentation/schemas/report.py).

Idempotent: a filter whose name already exists for that user is skipped (--force overrides).

Pre-requisites:
    uv run python scripts/seed_users.py
    API server must be running.

Usage:
    uv run python scripts/seed_saved_filters.py [--url URL] [--force]
"""
from __future__ import annotations

import argparse
import sys

import httpx

# Users that get saved filters (admin omitted — these are end-user presets).
FILTER_USERS: list[tuple[str, str]] = [
    ("citizen01@gavea.br", "citizen01pass"),
    ("citizen02@gavea.br", "citizen02pass"),
    ("citizen03@gavea.br", "citizen03pass"),
    ("citizen04@gavea.br", "citizen04pass"),
    ("citizen05@gavea.br", "citizen05pass"),
    ("agente@gavea.br", "agente12345"),
]

# Preset filters seeded for every user. Each body is a free dict mirroring the
# report-query schema; the frontend FilterPanel reads the same field names.
_PRESETS: list[dict] = [
    {"name": "Urgência alta", "body": {"urgencies": ["alta"], "limit": 50}},
    {
        "name": "Pendentes de iluminação",
        "body": {"statuses": ["pendente"], "q": "iluminação", "limit": 50},
    },
    {
        "name": "Encaminhados recentes",
        "body": {"statuses": ["encaminhado"], "limit": 50},
    },
]


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"  Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _existing_names(client: httpx.Client, token: str) -> set[str]:
    resp = client.get("/saved-filters", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        return set()
    return {sf["name"] for sf in resp.json()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed named saved filters per user.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--force", action="store_true", help="Create presets even if a same-named filter exists"
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")
    created = 0
    skipped = 0

    with httpx.Client(base_url=base, timeout=30) as client:
        for email, password in FILTER_USERS:
            token = _login(client, email, password)
            headers = {"Authorization": f"Bearer {token}"}
            existing = set() if args.force else _existing_names(client, token)

            for preset in _PRESETS:
                if preset["name"] in existing:
                    skipped += 1
                    continue
                resp = client.post(
                    "/saved-filters",
                    json={"name": preset["name"], "body": preset["body"]},
                    headers=headers,
                )
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    print(
                        f"  Error {resp.status_code} creating '{preset['name']}' for {email}: "
                        f"{resp.text}",
                        file=sys.stderr,
                    )
            print(f"  {email}: presets ensured")

    print(f"\nDone. Saved filters created: {created}, skipped (already existed): {skipped}")


if __name__ == "__main__":
    main()
