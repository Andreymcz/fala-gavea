"""Seed script: inserts dev users via the REST API, then promotes roles via the DB.

The /auth/register endpoint only creates citizens, so admin/agent promotion is done
with a direct DB update after registration.

Pre-requisites: API server must be running (for registration).

Usage:
    uv run python scripts/seed_users.py [--url http://localhost:8000]
"""
import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fala_gavea.infrastructure.database.models import UserModel
from fala_gavea.infrastructure.database.session import SessionLocal, create_tables

SEED_USERS = [
    {"email": "admin@gavea.br", "name": "Administrador", "password": "admin12345", "role": "admin"},
    {"email": "citizen01@gavea.br", "name": "Cidadao01", "password": "citizen01pass", "role": "citizen"},
    {"email": "agente@gavea.br", "name": "Agente Publico", "password": "agente12345", "role": "agent"},
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed users via the Fala Gávea API.")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    created = 0
    skipped = 0
    to_promote: list[tuple[str, str]] = []

    with httpx.Client(base_url=base, timeout=10) as client:
        for user in SEED_USERS:
            resp = client.post("/auth/register", json={
                "email": user["email"],
                "name": user["name"],
                "password": user["password"],
            })
            if resp.status_code in (200, 201):
                print(f"  Created: {user['email']} (registered as citizen)")
                created += 1
            elif resp.status_code == 409:
                print(f"  Skipped (already exists): {user['email']}")
                skipped += 1
            else:
                print(f"  Error {resp.status_code} for {user['email']}: {resp.text}", file=sys.stderr)
                continue

            if user["role"] != "citizen":
                to_promote.append((user["email"], user["role"]))

    # Promote roles that the API cannot set
    if to_promote:
        create_tables()
        session = SessionLocal()
        for email, role in to_promote:
            session.query(UserModel).filter_by(email=email).update({"role": role})
            print(f"  Promoted: {email} → {role}")
        session.commit()
        session.close()

    print(f"\nDone. Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
