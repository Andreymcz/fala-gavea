# QA Log | Implement 000170 | 2026-06-25 12:19 UTC | seed citizen01 test data and verify features

**Brief**: Implemented plan-000170 — created `scripts/seed_citizen01.py` with 10 relatos for citizen01@gavea.br (expanded from plan's 5) and a forwarding that mixes citizen01's relatos with up to 2 reports from other users, plus updated `scripts/seed_all.py` with Phase 5 and `--skip-citizen01` flag.

---

## Q1
User: `/implement 170, add more user relatos and when creating encaminhamento add relatos from other users`

## A1
Read plan-000170 (seed citizen01 test data). Plan specified 5 relatos + 1 forwarding with citizen01 relatos only. User's addendum:
- "add more user relatos" → expanded from 5 to 10 relatos for citizen01
- "when creating encaminhamento add relatos from other users" → forwarding now queries up to 2 pendente reports from other users (via `GET /reports/query` as agente) and appends them to the citizen01 report IDs

Implemented Step 1: created `scripts/seed_citizen01.py` with:
- 10 hardcoded relatos for citizen01 (varied urgency/type/location across Gavea bounding box)
- `_fetch_other_pendente_reports()` helper that queries pendente reports as agente, filters out citizen01's own IDs, returns up to 2
- Forwarding links citizen01 relatos [0-2] + up to 2 other-user reports; gracefully degrades if no other reports exist
- Idempotency guard via `GET /forwardings/mine`; `--force` override
- Human-readable summary printed at end

Implemented Step 2: updated `scripts/seed_all.py`:
- Added `--skip-citizen01` argument
- Added Phase 5 calling `seed_citizen01.py`
- Updated final summary block with citizen01 verification instructions (10 relatos expected, 1 forwarding)

Verified: `uv run python scripts/seed_all.py --help` shows `--skip-citizen01`; `uv run ruff check` → All checks passed.

Committed as `feat(seed): implement plan-000170 — citizen01 test data with 10 relatos + mixed-user forwarding`.
