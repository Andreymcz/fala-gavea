"""Seed script: curated journey-anchor relatos for the agent worklist demo.

Bulk-inserts a small, curated CSV of *dated, unresolved* relatos via the admin
endpoint POST /admin/seed/relatos (CSV upload, admin-only). These "anchors" exist
so the public-agent journey is demonstrable and deterministic: when an agent logs
in and queries the worklist (postes apagados/queimados + lixo + seguranca,
`pendente`, within the last 30 days), there is always a non-empty, curated set of
relatos to triage and forward.

WHY A SEPARATE PHASE (must run LAST):
    seed_all.py phase 3 (seed_forwardings.py) forwards a random ~50% sample of the
    pendente pool. Any relato created *before* that phase risks being swept into a
    forwarding and disappearing from the agent worklist. By running these anchors as
    the LAST phase (after lifecycle), they are guaranteed to stay `pendente` — the
    random sampler never sees them.

DEMO DATE (fixed): 2026-06-27.
    The anchor dates in data/seed_journey_anchors.csv span 2026-05-29 .. 2026-06-26,
    i.e. the 30-day window ending the day before the demo date. These are FIXED
    DATES, not relative to seed time. If the demo moves to a different month, the
    worklist (which filters on the last 30 days relative to *now*) will shrink —
    regenerate/shift the CSV dates accordingly. See seeds/relatos/SCHEMA.md.

Idempotent by default: if an anchor relato is already present (matched by a unique
canonical phrase), the script skips. Use --force to upload anyway.

Pre-requisites:
    uv run python scripts/seed_users.py
    API server must be running (admin bootstrap env vars set).
    (Report types are created automatically from each CSV row's `topico`.)

Usage:
    uv run python scripts/seed_journey_anchors.py [--url URL] [--csv PATH]
                                                  [--user EMAIL] [--password PWD]
                                                  [--force]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

DEFAULT_CSV = Path(__file__).parent.parent / "data" / "seed_journey_anchors.csv"

# A unique substring of the first anchor relato (row 1 of the CSV). Used as the
# idempotency probe: if /reports/query matches it, the anchors are already seeded.
# Must stay in sync with data/seed_journey_anchors.csv if that row is edited.
_CANONICAL_ANCHOR_PHRASE = (
    "Tres postes consecutivos apagados na Rua Professor Saboia Ribeiro"
)


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    if resp.status_code != 200:
        print(f"Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _anchors_already_present(client: httpx.Client, token: str) -> bool:
    """Return True if the canonical anchor relato already exists (idempotency probe)."""
    resp = client.post(
        "/reports/query",
        json={"text": _CANONICAL_ANCHOR_PHRASE, "limit": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        # Fail open: if the probe fails, do not block the upload (let it run).
        print(
            f"Warning: idempotency probe failed ({resp.status_code}); proceeding with upload.",
            file=sys.stderr,
        )
        return False
    return resp.json().get("total", 0) > 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk-insert curated journey-anchor relatos via the admin API."
    )
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to anchors CSV file")
    parser.add_argument("--user", default="admin@gavea.br", help="Admin email")
    parser.add_argument("--password", default="admin12345!", help="Admin password")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Upload even if the anchors appear to be already present",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    base = args.url.rstrip("/")
    size_kb = csv_path.stat().st_size // 1024

    with httpx.Client(base_url=base, timeout=120) as client:
        token = _login(client, args.user, args.password)

        # --- Idempotency guard ---
        if not args.force and _anchors_already_present(client, token):
            print("journey anchors already present — skipping (use --force to re-seed).")
            return

        # --- Bulk upload CSV ---
        print(f"  Uploading {csv_path.name} ({size_kb} KB)...")
        with csv_path.open("rb") as f:
            resp = client.post(
                "/admin/seed/relatos",
                files={"file": (csv_path.name, f, "text/csv")},
                headers={"Authorization": f"Bearer {token}"},
            )

        if resp.status_code not in (200, 201):
            print(f"Bulk insert failed ({resp.status_code}): {resp.text}", file=sys.stderr)
            sys.exit(1)

        result = resp.json()
        inserted = result.get("inserted", "?")
        skipped = result.get("skipped", "?")
        errors = result.get("errors", [])
        print(f"  Done. Inserted: {inserted}, Skipped: {skipped}, Errors: {len(errors)}")
        if errors:
            for e in errors[:5]:
                print(f"    Error: {e}", file=sys.stderr)
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more errors", file=sys.stderr)


if __name__ == "__main__":
    main()
