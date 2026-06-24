"""Orchestrator: run all seed scripts in dependency order.

Usage:
    uv run python scripts/seed_all.py [--url URL] [--count N] [--full] [--skip-forwardings]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

DEV_ACCOUNTS = [
    ("admin@gavea.br", "admin12345", "admin"),
    ("citizen01@gavea.br", "citizen01pass", "citizen"),
    ("agente@gavea.br", "agente12345", "agent"),
]


def run_phase(label: str, cmd: list[str], env: dict[str, str] | None = None) -> None:
    print(f"\n{'=' * 60}")
    print(f"  Phase: {label}")
    print(f"{'=' * 60}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print(f"\nPhase '{label}' failed (exit {result.returncode}). Aborting.", file=sys.stderr)
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all fala-gavea seed scripts in order.")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--count", type=int, default=100, help="Number of relatos to seed (default 100)")
    parser.add_argument("--full", action="store_true", help="Seed full corpus (10 000 relatos)")
    parser.add_argument("--skip-forwardings", action="store_true", help="Skip forwarding seed")
    args = parser.parse_args()

    count = 10_000 if args.full else args.count
    url = args.url

    py = sys.executable

    # Phase 1: users
    run_phase("Users (all roles)", [py, str(SCRIPTS_DIR / "seed_users.py"), "--url", url])

    # Phase 2: report types (env-var driven script)
    env = {
        **os.environ,
        "FALA_GAVEA_API_URL": url,
        "FALA_GAVEA_ADMIN_EMAIL": "admin@gavea.br",
        "FALA_GAVEA_ADMIN_PASSWORD": "admin12345",
    }
    run_phase("Report types", [py, str(SCRIPTS_DIR / "seed_report_types.py")], env=env)

    # Phase 3: relatos
    run_phase(
        f"Relatos ({count})",
        [py, str(SCRIPTS_DIR / "seed_relatos.py"), "--url", url, "--count", str(count)],
    )

    # Phase 4: forwardings (optional)
    if not args.skip_forwardings:
        run_phase("Forwardings", [py, str(SCRIPTS_DIR / "seed_forwardings.py"), "--url", url])
    else:
        print("\nSkipping forwardings (--skip-forwardings).")

    print("\n" + "=" * 60)
    print("  All seeds complete.")
    print("=" * 60)
    print("\nDev accounts (one per role):")
    for email, pwd, role in DEV_ACCOUNTS:
        print(f"  {email:<28} / {pwd:<18} (role: {role})")
    print()


if __name__ == "__main__":
    main()
