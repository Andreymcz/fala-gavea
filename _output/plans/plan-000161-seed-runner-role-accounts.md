# Plan 000161 | chore/scripts | 2026-06-24 11:51 UTC | seed runner and role accounts | Review: light
plan_format_version: 1

## Brief

Following roadmap 151, create a `scripts/seed_all.py` orchestrator that runs all existing seed scripts
in their required dependency order. Also confirm that one seeded account exists for every role:
admin, agent (public agent), and citizen.

## Context

Four seed scripts already exist in `scripts/`:

| Script | Purpose | Requires |
|--------|---------|---------|
| `seed_users.py` | 3 dev user accounts (one per role) via API + direct DB promote | API running |
| `seed_report_types.py` | 8 initial report types via admin API | admin user |
| `seed_relatos.py` | N reports (default 10 000) via API | report types + any auth user |
| `seed_forwardings.py` | sample forwardings via agent API | relatos + agent user |

Dependency chain: users → report_types → relatos → forwardings.

`seed_users.py` already seeds one account per role:
- `admin@gavea.br` / `admin12345` — role: admin  
- `citizen01@gavea.br` / `citizen01pass` — role: citizen  
- `agente@gavea.br` / `agente12345` — role: agent (public agent)

No changes needed to `seed_users.py` — role coverage is complete.

## Checklist

- [ ] Step 1 — Create `scripts/seed_all.py` orchestrator
- [ ] Step 2 — Manual smoke-test: run `uv run python scripts/seed_all.py --help`
- [ ] Step 3 — Update `CLAUDE.md` Build & Run section with the new command

---

## Step 1 — Create `scripts/seed_all.py`

**File**: `scripts/seed_all.py` (new)

Create an orchestrator script that:

1. Accepts CLI flags:
   - `--url URL` (default `http://localhost:8000`) — passed through to all sub-scripts
   - `--count N` (default `100`) — relatos count for dev; use `--count 10000` for full corpus
   - `--skip-forwardings` — skip the forwarding seed (useful when relatos is already seeded)
   - `--full` — shorthand that sets `--count 10000` (overrides `--count`)

2. Runs each script phase via `subprocess.run([sys.executable, script_path, ...args])`:
   - Phase 1: users
   - Phase 2: report_types (env-var driven; pass `FALA_GAVEA_API_URL`, `FALA_GAVEA_ADMIN_EMAIL`, `FALA_GAVEA_ADMIN_PASSWORD`)
   - Phase 3: relatos
   - Phase 4: forwardings (skipped if `--skip-forwardings`)

3. Prints a phase header before each step (`=== Phase N: <name> ===`) and exits with a non-zero code if any phase fails (hard dependency chain).

4. On success, prints a summary block:
   ```
   ✓ All seeds complete.
   
   Dev accounts:
     admin@gavea.br      / admin12345      (role: admin)
     citizen01@gavea.br  / citizen01pass   (role: citizen)
     agente@gavea.br     / agente12345     (role: agent)
   ```

**Implementation notes**:
- Use `pathlib.Path(__file__).parent` to resolve sibling script paths (no hardcoded paths).
- `seed_report_types.py` reads env vars; build `env = {**os.environ, "FALA_GAVEA_API_URL": url, "FALA_GAVEA_ADMIN_EMAIL": "admin@gavea.br", "FALA_GAVEA_ADMIN_PASSWORD": "admin12345"}` and pass `env=env` to subprocess.
- `seed_relatos.py` and `seed_forwardings.py` use argparse `--url`; pass `["--url", url, ...]` as args.
- `seed_users.py` uses argparse `--url`; pass `["--url", url]`.

```python
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
```

**Test**: `uv run python scripts/seed_all.py --help` should print usage without errors.

---

## Step 2 — Smoke-test

Run once with `--skip-forwardings` and `--count 5` against a live server to confirm phase headers print, each sub-script exits 0, and the summary block appears.

```bash
uv run uvicorn fala_gavea.presentation.api.main:app --reload &
uv run python scripts/seed_all.py --count 5 --skip-forwardings
```

Expected: 3 phases succeed, summary block shows the 3 dev account entries.

---

## Step 3 — Update `CLAUDE.md`

In `CLAUDE.md § Build & Run`, add the seed runner under the API server line:

```markdown
# Seed all data (users + report types + relatos + forwardings)
uv run python scripts/seed_all.py [--count N] [--full] [--skip-forwardings]
```

---

## Review (light)

| Perspective | Finding |
|------------|---------|
| Correctness | Subprocess exit-code propagation ensures hard failures stop the chain. env passthrough to seed_report_types.py preserves its required env vars. `sys.executable` avoids venv mismatch. |
| Security | No new endpoints or auth flows. Dev credentials are already in seed_users.py; no new exposure. |
| Simplicity | Thin orchestrator — no new abstractions, all logic stays in existing seed scripts. |

---

## Files Changed

| File | Change |
|------|--------|
| `scripts/seed_all.py` | New — seed orchestrator |
| `CLAUDE.md` | Minor — add seed runner command to Build & Run |

---

## Docs

No new documentation needed beyond the `CLAUDE.md` update.
