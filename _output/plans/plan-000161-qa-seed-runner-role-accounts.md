# QA Log | Plan 000161 | 2026-06-24 11:54 UTC | seed runner and role accounts

**Brief**: Plan session for creating a `scripts/seed_all.py` orchestrator that runs all existing seed scripts in dependency order, and confirming one seeded account per role (admin, agent, citizen).

---

## Q1

Folowing roadmap 151 i want to run a seed script that will run all seeds existing. also i want to have a account for every possible role: admin, public agent and citzen seeded

## A1

Loaded project context (as-coded, as-intended, conventions). Identified 4 existing seed scripts:
- `scripts/seed_users.py` — already seeds all 3 roles (admin@gavea.br, citizen01@gavea.br, agente@gavea.br)
- `scripts/seed_report_types.py` — 8 initial report types via admin API
- `scripts/seed_relatos.py` — N reports via API
- `scripts/seed_forwardings.py` — sample forwardings via agent API

Generated Plan 000161: create `scripts/seed_all.py` — a thin orchestrator that runs all four scripts in dependency order (users → report_types → relatos → forwardings) via `subprocess.run`, with phase headers, failure propagation, and a dev-account summary block. Includes `--count` (default 100), `--full` (10 000), and `--skip-forwardings` flags. No changes needed to existing seed scripts — role coverage is already complete.
