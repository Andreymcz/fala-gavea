# QA Log | Plan 000170 | 2026-06-25 12:09 UTC | seed citizen01 test data and verify features

**Brief:** seed citizen01@gavea.br. I want to log in as citizen01 and see my relatos and encaminhamentos. update seed scripts in order to create this test data and check the features weve implemented

---

## Q1

seed citizen01@gavea.br. I want to log inas citzen01 and see my relatos and encaminhamentos. update seed scripts in order to create this test data and check the features weve implemented

## A1

Ran pre-skill (brief-log, budget-eval, ref-load, constitution). Loaded eager references: product-design-as-coded.md, product-design-as-intended.md. Loaded briefs index. Reserved plan ID 000170.

Analyzed the gap: `citizen01@gavea.br` is created by `seed_users.py` but all CSV-seeded reports go to synthetic `{user_id}@seed.gavea.br` accounts. So citizen01 has zero authored relatos and consequently zero results in "Meus relatos" and "Meus encaminhamentos".

Generated Plan 000170 (CHORE-X, light review) with 2 steps:

- **Step 1**: Create `scripts/seed_citizen01.py` -- logs in as citizen01, creates 5 relatos (Gavea coords, varied types/urgencies), then logs in as agente and creates 1 forwarding linking relatos 1-3. Idempotency guard via `GET /forwardings/mine`.
- **Step 2**: Update `scripts/seed_all.py` -- add Phase 5 "Citizen01 test data" + `--skip-citizen01` flag + updated summary block with verification instructions.

Plan includes a manual verification checklist covering "Meus relatos" workspace toggle and "Meus encaminhamentos" toggle on /encaminhamentos.

Filed implement pending entry pa-000062 for plan-000170.
