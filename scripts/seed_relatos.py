"""Seed script: bulk-insert reports from CSV via the admin API endpoint.

Uses POST /admin/seed/relatos (CSV file upload, admin-only).
Default CSV: data/seed_relatos_fala_gavea_5k.csv

Pre-requisites:
    uv run python scripts/seed_users.py
    API server must be running.
    (Report types are created automatically from each CSV row's `topico`.)

Usage:
    uv run python scripts/seed_relatos.py [--url URL] [--csv PATH]
                                           [--user EMAIL] [--password PWD]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

DEFAULT_CSV = Path(__file__).parent.parent / "data" / "seed_relatos_fala_gavea_5k.csv"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk-insert reports from CSV via the admin API."
    )
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to CSV file")
    parser.add_argument("--user", default="admin@gavea.br", help="Admin email")
    parser.add_argument("--password", default="admin12345!", help="Admin password")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    base = args.url.rstrip("/")
    size_kb = csv_path.stat().st_size // 1024

    with httpx.Client(base_url=base, timeout=120) as client:
        # Login as admin
        resp = client.post(
            "/auth/token",
            data={"username": args.user, "password": args.password},
        )
        if resp.status_code != 200:
            print(f"Login failed ({resp.status_code}): {resp.text}", file=sys.stderr)
            sys.exit(1)
        token = resp.json()["access_token"]

        # Bulk upload CSV
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
