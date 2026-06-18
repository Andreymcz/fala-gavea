# QA Log | Plan 000085 | 2026-06-18 17:38 UTC | seed relatos 1 ano

**Brief**: Implement plan-000085 — create `seed_relatos.py` that reads scenario CSVs (or falls back to 35 built-in templates) and replicates a corpus of ~10 000 reports with lat/lon and date jitter across a 1-year window, inserting directly into SQLite. Also includes `seeds/relatos/SCHEMA.md` contract for collaborator Herbert and `seed_users.py` (prerequisite from plan-000084 that had not yet been implemented).

---

## Q1

`/implement 85`

## A1

Ran `/pre-skill implement 85`. Resolved plan-000085 from INDEX.md. Read plan file: 2 steps — (1) create `seeds/relatos/SCHEMA.md` + `.gitkeep`, (2) create `scripts/seed_relatos.py`. Created rollback branch `pre-plan-000085`. Discovered `seed_users.py` (plan-000084 prerequisite) was never implemented despite being planned. Read models, session, domain entities, and password service to understand import paths.

## Q2

*(internal — skill execution)*

Execute Step 1: Create `seeds/relatos/` directory, `SCHEMA.md` (full CSV contract with eixo-temático guidance for Herbert), and `.gitkeep`.

## A2

Created `seeds/relatos/SCHEMA.md` and `seeds/relatos/.gitkeep`. Step 1 complete.

## Q3

*(internal — skill execution)*

Execute prerequisite: create `scripts/seed_users.py` (plan-000084 unimplemented).

## A3

Created `scripts/seed_users.py` using `SQLAlchemyUserRepository` + `PasswordService`. Seeds 3 dev users: admin@gavea.br (admin), citizen01@gavea.br (citizen), agente@gavea.br (agent), passwords equal to username prefix. Idempotent via `find_by_email` guard. Verified: `Done. Created: 3, Skipped: 0` on fresh DB; re-run → `Done. Created: 0, Skipped: 3`.

## Q4

*(internal — skill execution)*

Execute Step 2: Create `scripts/seed_relatos.py`.

## A4

Created `scripts/seed_relatos.py` with:
- `load_csv_corpus()`: reads `*.csv` from `--csv-dir`, resolves `id_cidadao → author_id` via `{id}@gavea.br` email lookup, `topico → report_type_id` case-insensitive dict, parses ISO 8601 dates.
- `build_synthetic_corpus()`: 35 built-in texts organized by 8 research-connection eixos (saneamento/saúde, iluminação/segurança, espaço público/conflito, etc.).
- `jitter_date()`: ±15 days + random hour, clamped to past-year window.
- `weighted_choice()`: urgency (alta 15%, media 60%, baixa 25%), status (pendente 50%, em_analise 25%, encaminhado 15%, resolvido 10%).
- Idempotency guard: skip if `existing >= count // 2` unless `--force`.
- `bulk_save_objects` for batch insert.

## Q5

*(internal — verification)*

Ran `uv run python scripts/seed_relatos.py --count 100` → `Done. Created: 100 reports over the past 365 days.`
Re-run → `Skip: 100 reports already in DB. Use --force to re-seed.`
`--force --count 100` → `Done. Created: 100 reports over the past 365 days.`
SQLite check: `SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM reports` → `(200, '2025-06-18 17:34:08...', '2026-06-18 17:34:08...')`.
All Verify criteria met. Committed: `feat(scripts): add seed_relatos.py with CSV ingestion and 10k replication`.

## A5

Both steps complete. Plan marked DONE. Pending ledger updated.
