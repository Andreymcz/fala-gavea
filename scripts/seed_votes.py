"""Seed script: cast up/down votes on reports and forwardings via the REST API.

Votes are one of the features with no seed today. This script logs in a pool of
non-admin voters (citizen01–citizen05 + agente), samples reports and forwardings,
and casts weighted-random votes on them.

Robustness:
  - 409 (SelfVoteError): a voter cannot vote on their own content — skipped silently.
  - 429 (rate limit, 20/minute per user): exponential backoff (2->4->8s), then skip.
A repeat cast is an upsert (no duplicate vote), so re-running is safe.

Pre-requisites:
    uv run python scripts/seed_users.py
    uv run python scripts/seed_report_types.py
    uv run python scripts/seed_relatos.py
    uv run python scripts/seed_forwardings.py   (for forwarding votes)
    API server must be running.

Usage:
    uv run python scripts/seed_votes.py [--url URL] [--seed 42] [--force]
                                        [--max-reports 40]
"""
from __future__ import annotations

import argparse
import random
import sys
import time

import httpx

# (email, password) of users allowed to vote. Admin is excluded so the seed does
# not repeatedly self-vote on the admin-authored bulk relatos.
VOTERS: list[tuple[str, str]] = [
    ("citizen01@gavea.br", "citizen01pass"),
    ("citizen02@gavea.br", "citizen02pass"),
    ("citizen03@gavea.br", "citizen03pass"),
    ("citizen04@gavea.br", "citizen04pass"),
    ("citizen05@gavea.br", "citizen05pass"),
    ("agente@gavea.br", "agente12345"),
]

# Weighted vote outcome per (voter, target): upvote / downvote / skip.
_UPVOTE_WEIGHT = 0.70
_DOWNVOTE_WEIGHT = 0.15
# remaining 0.15 -> skip


def _login(client: httpx.Client, email: str, password: str) -> str:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"  Login failed for {email} ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()["access_token"]


def _login_all(client: httpx.Client) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for email, password in VOTERS:
        tokens[email] = _login(client, email, password)
    return tokens


def _fetch_reports(client: httpx.Client, token: str, limit: int) -> list[str]:
    resp = client.post(
        "/reports/query",
        json={"statuses": ["pendente", "encaminhado"], "limit": limit, "offset": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code != 200:
        print(f"Error querying reports ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)
    return [r["id"] for r in resp.json().get("items", [])]


def _fetch_forwardings(client: httpx.Client, token: str) -> list[str]:
    resp = client.get("/forwardings", headers={"Authorization": f"Bearer {token}"})
    if resp.status_code != 200:
        print(
            f"Warning: could not fetch forwardings ({resp.status_code}); skipping forwarding votes.",
            file=sys.stderr,
        )
        return []
    return [f["id"] for f in resp.json()]


class _Counters:
    def __init__(self) -> None:
        self.cast = 0
        self.self_skipped = 0
        self.rate_limited = 0
        self.errors = 0


def _cast(
    client: httpx.Client,
    path: str,
    token: str,
    value: int,
    counters: _Counters,
) -> None:
    """POST a vote, handling 409 (self-vote) and 429 (rate limit) gracefully."""
    headers = {"Authorization": f"Bearer {token}"}
    backoff = 2
    for _attempt in range(3):
        resp = client.post(path, json={"value": value}, headers=headers)
        if resp.status_code == 200:
            counters.cast += 1
            return
        if resp.status_code == 409:  # SelfVoteError
            counters.self_skipped += 1
            return
        if resp.status_code == 429:  # rate limit (20/minute per user)
            counters.rate_limited += 1
            time.sleep(backoff)
            backoff *= 2
            continue
        counters.errors += 1
        print(f"  Error {resp.status_code} on {path}: {resp.text}", file=sys.stderr)
        return


def _vote_value(rng: random.Random) -> int | None:
    roll = rng.random()
    if roll < _UPVOTE_WEIGHT:
        return 1
    if roll < _UPVOTE_WEIGHT + _DOWNVOTE_WEIGHT:
        return -1
    return None  # skip


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed votes on reports and forwardings.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--max-reports", type=int, default=40, help="Max reports to vote on")
    parser.add_argument(
        "--force",
        action="store_true",
        help="(reserved) re-cast even if summaries are already populated; casts are upserts either way",
    )
    args = parser.parse_args()

    base = args.url.rstrip("/")
    rng = random.Random(args.seed)
    counters = _Counters()

    with httpx.Client(base_url=base, timeout=30) as client:
        tokens = _login_all(client)
        print(f"Logged in {len(tokens)} voter(s).")

        any_token = next(iter(tokens.values()))
        # GET /forwardings is agent/admin-only — list with the agent token, not a
        # citizen's, or it 403s and forwarding votes are silently skipped.
        agent_token = tokens.get("agente@gavea.br", any_token)
        report_ids = _fetch_reports(client, any_token, args.max_reports)
        forwarding_ids = _fetch_forwardings(client, agent_token)
        print(f"Targets: {len(report_ids)} report(s), {len(forwarding_ids)} forwarding(s).")

        for rid in report_ids:
            for email, token in tokens.items():
                value = _vote_value(rng)
                if value is None:
                    continue
                _cast(client, f"/reports/{rid}/votes", token, value, counters)

        for fid in forwarding_ids:
            for email, token in tokens.items():
                value = _vote_value(rng)
                if value is None:
                    continue
                _cast(client, f"/forwardings/{fid}/votes", token, value, counters)

    print(
        f"\nDone. Votes cast: {counters.cast}, self-skipped (409): {counters.self_skipped}, "
        f"rate-limited retries (429): {counters.rate_limited}, errors: {counters.errors}"
    )


if __name__ == "__main__":
    main()
