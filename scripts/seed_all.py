"""Orchestrator: run all seed scripts in dependency order.

Pre-requisite: API must be running with admin bootstrap env vars:
    FALA_GAVEA_ADMIN_EMAIL=admin@gavea.br
    FALA_GAVEA_ADMIN_PASSWORD=admin12345!

Profiles:
    showcase (default) — curated, fast, deterministic; uses the 200-row CSV and
                         seeds every feature (votes, comments, saved filters,
                         forwarding lifecycle). Ideal for demos.
    full              — heavier/realistic volume; uses the 5k-row CSV. Feature
                        phases still run.

Usage:
    uv run python scripts/seed_all.py [--url URL] [--profile showcase|full] [--csv PATH]
                                      [--skip-forwardings] [--skip-citizen01]
                                      [--skip-votes] [--skip-comments]
                                      [--skip-saved-filters] [--skip-lifecycle]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = SCRIPTS_DIR.parent / "data"
SHOWCASE_CSV = str(DATA_DIR / "seed_relatos_fala_gavea_200.csv")
FULL_CSV = str(DATA_DIR / "seed_relatos_fala_gavea_5k.csv")

DEV_ACCOUNTS = [
    ("admin@gavea.br", "admin12345!", "admin"),
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
    parser.add_argument(
        "--profile",
        choices=["showcase", "full"],
        default="showcase",
        help="showcase (curated 200-row, default) or full (5k-row)",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV file for relatos bulk insert (overrides the profile default)",
    )
    parser.add_argument("--skip-forwardings", action="store_true", help="Skip forwarding seed")
    parser.add_argument("--skip-citizen01", action="store_true", help="Skip citizen01 test data seed")
    parser.add_argument("--skip-votes", action="store_true", help="Skip votes seed")
    parser.add_argument("--skip-comments", action="store_true", help="Skip comments seed")
    parser.add_argument("--skip-saved-filters", action="store_true", help="Skip saved-filters seed")
    parser.add_argument("--skip-lifecycle", action="store_true", help="Skip forwarding-lifecycle seed")
    args = parser.parse_args()

    url = args.url
    py = sys.executable

    # Resolve CSV: explicit --csv wins, otherwise pick by profile.
    csv = args.csv or (FULL_CSV if args.profile == "full" else SHOWCASE_CSV)
    print(f"Profile: {args.profile}  |  CSV: {csv}")

    # Phase 1: users (incl. extra citizens for cross-user votes/comments)
    run_phase("Users (all roles)", [py, str(SCRIPTS_DIR / "seed_users.py"), "--url", url])

    # Phase 2: relatos (bulk upload CSV as admin). Report types are created
    # automatically from each row's `topico` during bulk insert, so there is no
    # separate report-types phase.
    run_phase(
        "Relatos (bulk from CSV)",
        [py, str(SCRIPTS_DIR / "seed_relatos.py"), "--url", url, "--csv", csv],
    )

    # Phase 3: forwardings (optional)
    if not args.skip_forwardings:
        run_phase("Forwardings", [py, str(SCRIPTS_DIR / "seed_forwardings.py"), "--url", url])
    else:
        print("\nSkipping forwardings (--skip-forwardings).")

    # Phase 4: citizen01 test data (optional)
    if not args.skip_citizen01:
        run_phase(
            "Citizen01 test data",
            [py, str(SCRIPTS_DIR / "seed_citizen01.py"), "--url", url],
        )
    else:
        print("\nSkipping citizen01 test data (--skip-citizen01).")

    # Phase 5: votes (needs relatos + forwardings)
    if not args.skip_votes:
        run_phase("Votes", [py, str(SCRIPTS_DIR / "seed_votes.py"), "--url", url])
    else:
        print("\nSkipping votes (--skip-votes).")

    # Phase 6: comments (needs forwardings)
    if not args.skip_comments:
        run_phase("Comments", [py, str(SCRIPTS_DIR / "seed_comments.py"), "--url", url])
    else:
        print("\nSkipping comments (--skip-comments).")

    # Phase 7: saved filters (needs users)
    if not args.skip_saved_filters:
        run_phase("Saved filters", [py, str(SCRIPTS_DIR / "seed_saved_filters.py"), "--url", url])
    else:
        print("\nSkipping saved filters (--skip-saved-filters).")

    # Phase 8: forwarding lifecycle (needs forwardings)
    if not args.skip_lifecycle:
        run_phase(
            "Forwarding lifecycle",
            [py, str(SCRIPTS_DIR / "seed_forwarding_lifecycle.py"), "--url", url],
        )
    else:
        print("\nSkipping forwarding lifecycle (--skip-lifecycle).")

    print("\n" + "=" * 60)
    print("  All seeds complete.")
    print("=" * 60)
    print("\nDev accounts (one per role):")
    for email, pwd, role in DEV_ACCOUNTS:
        print(f"  {email:<28} / {pwd:<18} (role: {role})")
    print("  citizen02..05@gavea.br      / citizenNNpass      (role: citizen)")
    print()
    print("Verify showcase features:")
    print("  Login as citizen01@gavea.br / citizen01pass")
    print("  - Workspace (/): toggle 'Meus relatos'           -> citizen01 relatos visible")
    print("  - Open a relato dialog                           -> vote counts populated")
    print("  - Encaminhamentos (/encaminhamentos)             -> comments + lifecycle states")
    print("    (some forwardings 'solucao_em_andamento' / 'finalizado')")
    print("  - Filter panel                                   -> saved filters available")
    print()


if __name__ == "__main__":
    main()
