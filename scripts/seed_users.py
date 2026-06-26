"""Seed dev users via the REST API (no direct DB access).

Creates the dev accounts:
  admin@gavea.br        / admin12345!   — admin   (bootstrapped by server env vars)
  citizen01@gavea.br    / citizen01pass — citizen
  citizen02..05@gavea.br/ citizenNNpass — citizen (extra voters/commenters for showcase)
  agente@gavea.br       / agente12345   — agent

The extra citizen02–citizen05 accounts give the showcase seed enough distinct
identities for cross-user votes/comments (the vote API rejects self-votes, so
voters must differ from the content author).

The admin account must already exist in the API database, created automatically
by the server on startup via BootstrapAdminUser env vars:
  FALA_GAVEA_ADMIN_EMAIL=admin@gavea.br
  FALA_GAVEA_ADMIN_PASSWORD=admin12345!

seed_users.py registers the non-admin accounts and promotes the agent's role via
PATCH /auth/admin/users/{email}/role (admin-only endpoint).

Usage:
    uv run python scripts/seed_users.py [--url http://localhost:8000]
"""
from __future__ import annotations

import argparse
import sys

import httpx

# citizen01–citizen05 plus the agent. The extra citizens (02–05) exist so the
# showcase seed can cast cross-user votes/comments without tripping the
# self-vote guard (a user cannot vote on their own content).
NON_ADMIN_USERS = [
    {"email": "citizen01@gavea.br", "name": "Cidadao01", "password": "citizen01pass"},
    {"email": "citizen02@gavea.br", "name": "Cidadao02", "password": "citizen02pass"},
    {"email": "citizen03@gavea.br", "name": "Cidadao03", "password": "citizen03pass"},
    {"email": "citizen04@gavea.br", "name": "Cidadao04", "password": "citizen04pass"},
    {"email": "citizen05@gavea.br", "name": "Cidadao05", "password": "citizen05pass"},
    {"email": "agente@gavea.br", "name": "Agente Publico", "password": "agente12345"},
]

ADMIN_EMAIL = "admin@gavea.br"
ADMIN_PASSWORD = "admin12345!"

AGENT_EMAIL = "agente@gavea.br"


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"  Login failed ({resp.status_code}) for {email}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dev users via the Fala Gávea API.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    created = 0
    skipped = 0

    with httpx.Client(base_url=base, timeout=15) as client:
        # Step 1: register non-admin accounts (they start as citizen)
        for user in NON_ADMIN_USERS:
            resp = client.post(
                "/auth/register",
                json={"email": user["email"], "name": user["name"], "password": user["password"]},
            )
            if resp.status_code in (200, 201):
                print(f"  Created: {user['email']}")
                created += 1
            elif resp.status_code == 409:
                print(f"  Skipped (already exists): {user['email']}")
                skipped += 1
            else:
                print(
                    f"  Error {resp.status_code} for {user['email']}: {resp.text}",
                    file=sys.stderr,
                )

        # Step 2: login as admin (must be bootstrapped via server env vars)
        print(f"  Logging in as admin ({ADMIN_EMAIL})...")
        admin_token = _login(client, ADMIN_EMAIL, ADMIN_PASSWORD)

        # Step 3: promote agent role via admin-only API endpoint
        resp = client.patch(
            f"/auth/admin/users/{AGENT_EMAIL}/role",
            json={"role": "agent"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if resp.status_code == 200:
            print(f"  Promoted: {AGENT_EMAIL} → agent")
        elif resp.status_code == 404:
            print(
                f"  Warning: {AGENT_EMAIL} not found for promotion (registration may have failed)",
                file=sys.stderr,
            )
        else:
            print(
                f"  Error promoting {AGENT_EMAIL} ({resp.status_code}): {resp.text}",
                file=sys.stderr,
            )

    print(f"\nDone. Created: {created}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
