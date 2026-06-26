# DONE | 2026-06-26 20:33 UTC | Plan 000183 | TOOLING-X | 2026-06-26 20:20 | Local showcase seed pipeline + feature seeds (votes/comments/saved-filters/lifecycle) | Review: light
plan_format_version: 1

## Brief

create local pipeline for seeding app. create makefile entry receiving url as parameter and create a intial seed of the appplication to showcase features. There is some features that do not have any seed, like upvotes. check recent reflection to see what whas implemented and give suggestions of new seed pipeline entryes

## Agent Interpretation

Build a one-command local seed pipeline that produces a **curated showcase dataset** exercising every user-facing feature — including the ones with no seed today. Concretely:

1. A `make seed URL=...` target (URL parameterized, default `http://localhost:8000`) that drives the existing `seed_all.py` orchestrator in a new **`showcase` profile** (small/curated, deterministic, fast — uses the 200-row CSV, not the 5k).
2. New seed scripts for the currently-unseeded features, all going through the **REST API** (per the project convention that seeds never touch ChromaDB/DB directly): **votes** (the explicitly-named gap), **comments** on forwardings, **saved filters**, and **forwarding lifecycle advancement** (the real "resolved" showcase).
3. Extra **citizen accounts** so votes/comments look realistic across distinct users (the `SelfVoteError` guard blocks voting on your own content, so voters must differ from authors).
4. All new phases wired into `seed_all.py` and documented (Makefile `help`, `CLAUDE.md`).

### Gap analysis (from reflection-000163 + router survey)

| Feature | Endpoint | Seeded today? |
|---|---|---|
| Users | `POST /auth/register`, `PATCH /auth/admin/users/{email}/role` | Yes — 3 accounts |
| Report types | `POST /report_types` (seed_report_types.py) | Yes |
| Relatos (bulk) | `POST /admin/seed/relatos` (CSV, admin-authored) | Yes |
| Forwardings | `POST /forwardings` | Yes (~50% sample) |
| citizen01 test data | scripts | Yes |
| **Votes (up/down)** | `POST /reports/{id}/votes`, `POST /forwardings/{id}/votes` | **No** |
| **Comments** | `POST /forwardings/{id}/comments` | **No** |
| **Saved filters** | `POST /saved-filters` | **No** |
| **Forwarding lifecycle** | `PATCH /forwardings/{id}/status` (`solucao_em_andamento`, `finalizado`) | **No** |

### Findings worth surfacing (not blockers)

- **`ReportStatus.resolvido` is vestigial.** The enum value exists (`report.py:19`, DB `models.py:54`, LLM filter parser) but **no API path transitions a report to `resolvido`** — `create_forwarding` sets `encaminhado`; `update_forwarding_status` only mutates the forwarding. The app's real "resolved" concept is the **forwarding** reaching `finalizado`. The lifecycle seed (Step 5) therefore advances *forwardings*, not reports. Marking reports `resolvido` would require either a new endpoint or a direct DB write (the latter violates the API-only seed convention) — out of scope; noted under Suggestions.
- **Vote rate limit is `20/minute` per user** (`votes.py`, keyed by user id). The votes seed must spread casts across the voter pool and handle HTTP 429 with backoff so a re-run or a dense showcase doesn't abort.
- **Self-vote guard (409 `SelfVoteError`).** Bulk relatos are admin-authored and citizen01's relatos are citizen01-authored; the votes seed catches 409 and skips rather than pre-resolving authorship.

## Constraints & Conventions

- **API-only seeds.** Every new script authenticates and mutates via the REST API (httpx), matching `seed_votes`/`seed_comments`/etc. to the existing `seed_*.py` pattern. No direct SQLAlchemy/Chroma access (`CONVENTION_1`).
- **Idempotent / re-runnable.** Each script guards against duplicate work where the API allows it (votes upsert; comments check existing count; saved filters check by name; lifecycle skips already-advanced forwardings) and treats 409/429 as soft-skip.
- **Type annotations** on all functions (`CONVENTION_3`).
- **No hardcoded URL** — every script takes `--url` (default `http://localhost:8000`); the Makefile passes `URL`.
- Standards: `product-design/project/standards.md § Backend` (Python style for the scripts).

## Files

### Created
- `scripts/seed_votes.py` — cast up/down votes on reports + forwardings from non-author voters.
- `scripts/seed_comments.py` — add citizen/agent comments to a subset of forwardings.
- `scripts/seed_saved_filters.py` — create 1–2 named saved filters per non-admin user.
- `scripts/seed_forwarding_lifecycle.py` — advance a subset of forwardings to `solucao_em_andamento` / `finalizado`.

### Modified
- `scripts/seed_users.py` — add extra citizen accounts (citizen02–citizen05).
- `scripts/seed_all.py` — add `--profile {showcase,full}`, wire the 4 new phases, set the showcase CSV default.
- `Makefile` — add `seed` target taking `URL` (+ `PROFILE`), update `help`.
- `CLAUDE.md` (fala-gavea) — document `make seed` and the new seed phases under Build & Run.

## Steps

### Step 1: Add extra citizen accounts to seed_users.py
Extend the user seed so the showcase has enough distinct identities for cross-user votes/comments. Add `citizen02@gavea.br` … `citizen05@gavea.br` (password `citizenNNpass`, name `CidadaoNN`) to the `NON_ADMIN_USERS` list (keep `citizen01` and `agente`). Registration already returns 409 for existing users and the script counts that as "skipped" — so this stays idempotent. Only `agente@gavea.br` is promoted to the `agent` role; the new accounts remain `citizen`. Update the script docstring to list the new accounts.
- **Files**: `scripts/seed_users.py` (modify)
- **References**: `product-design/project/standards.md § Backend`
- **Interface**: same module API (`main()` CLI with `--url`); `NON_ADMIN_USERS` now has 5 citizens + 1 agent.
- **Verify**: `uv run python scripts/seed_users.py --url http://localhost:8000` creates/【skips citizen01–05 + agente; agente promoted to agent. Re-run reports all "Skipped".
- **Tests**: N/A — API-driven seed script with a live-server prerequisite (consistent with existing `seed_*.py`, which carry no unit tests); covered by the Verify run.

### Step 2: seed_votes.py — votes on reports and forwardings
Create a standalone script (mirror `seed_forwardings.py` structure) that:
- Logs in the **voter pool**: `agente`, `citizen01`–`citizen05` (skip admin as a voter to avoid voting on admin-authored bulk relatos repeatedly hitting 409). Collect `{email: token}`.
- Fetches a sample of reports via `POST /reports/query` (showcase: `statuses=["pendente","encaminhado"]`, `limit` ~40) and the forwardings via `GET /forwardings`.
- For each target, iterate the voter pool: cast a vote with weighted randomness (~70% upvote `value=1`, ~15% downvote `value=-1`, ~15% skip) via `POST /reports/{id}/votes` / `POST /forwardings/{id}/votes` with body `{"value": ...}`.
- **Robustness (required):** catch HTTP **409** (`SelfVoteError`) → skip silently; catch HTTP **429** (rate limit, `20/minute` per user) → exponential backoff (e.g., sleep 2→4→8s, max 3 retries) then skip. Use a fixed `--seed` (default 42) for reproducibility. Args: `--url`, `--seed`, `--force` (re-cast even if summaries already non-zero).
- Idempotency: a repeat cast is an upsert (no duplicate), so re-running is safe; `--force` is mostly cosmetic. Print a summary (votes cast, 409 skipped, 429 backed-off).
- **Files**: `scripts/seed_votes.py` (create)
- **References**: `product-design/project/standards.md § Backend`; vote API in `src/fala_gavea/presentation/api/routers/votes.py`; request schema `src/fala_gavea/presentation/schemas/votes.py` (`CastVoteRequest.value: int`).
- **Interface**: `main()` CLI: `--url`, `--seed`, `--force`.
- **Verify**: after `seed_relatos`/`seed_forwardings`, run the script; then `GET /reports/{id}/votes` for a sampled report returns `upvotes`/`downvotes` > 0. No unhandled 409/429.
- **Tests**: N/A — live-API seed tooling (see Step 1 rationale).

### Step 3: seed_comments.py — comments on forwardings
Create a standalone script that logs in `citizen01`–`citizen05` + `agente`, fetches forwardings via `GET /forwardings`, and for a subset (showcase: first ~6 forwardings) posts 1–3 short pt-BR comments each from rotating non-author users via `POST /forwardings/{id}/comments` (body `{"text": ...}`). Use a small curated bank of realistic comments ("Alguma previsão de prazo?", "Mesma situação na minha rua.", "Equipe esteve no local hoje, obrigado."). Idempotency: before posting, `GET /forwardings/{id}/comments`; skip the forwarding if it already has comments (unless `--force`). This also gives the forwarding **comment-synthesis** feature (plan-000179) real input. Args: `--url`, `--force`.
- **Files**: `scripts/seed_comments.py` (create)
- **References**: `product-design/project/standards.md § Backend`; comment API `src/fala_gavea/presentation/api/routers/comments.py`; schema `src/fala_gavea/presentation/schemas/comments.py` (`AddCommentRequest.text`).
- **Interface**: `main()` CLI: `--url`, `--force`.
- **Verify**: run the script; `GET /forwardings/{id}/comments` for a seeded forwarding returns ≥1 comment. Re-run prints "skipped (already has comments)".
- **Tests**: N/A — live-API seed tooling.

### Step 4: seed_saved_filters.py — named saved filters per user
Create a standalone script that logs in each non-admin user and creates 1–2 named saved filters via `POST /saved-filters` (body `{"name": str, "body": {...}}`). The `body` is a free `dict` that mirrors the report-query shape (`report_type_ids`, `urgencies`, `statuses`, `q`, `limit`, `offset` — see `src/fala_gavea/presentation/schemas/report.py`). Seed a few useful presets, e.g. `{"name": "Urgência alta", "body": {"urgencies": ["alta"], "limit": 50}}`, `{"name": "Pendentes de iluminação", "body": {"statuses": ["pendente"], "q": "iluminação"}}`. Idempotency: `GET /saved-filters`, skip a filter whose `name` already exists for that user. Args: `--url`, `--force`.
- **Files**: `scripts/seed_saved_filters.py` (create)
- **References**: `product-design/project/standards.md § Backend`; saved-filter API `src/fala_gavea/presentation/api/routers/saved_filters.py`; schema `src/fala_gavea/presentation/schemas/saved_filter.py` (`SavedFilterCreate.name`/`.body`); query field names in `src/fala_gavea/presentation/schemas/report.py`.
- **Interface**: `main()` CLI: `--url`, `--force`.
- **Verify**: run the script; `GET /saved-filters` as citizen01 returns ≥1 named filter. Re-run skips existing names.
- **Tests**: N/A — live-API seed tooling.

### Step 5: seed_forwarding_lifecycle.py — advance forwardings (the "resolved" showcase)
Create a standalone script that logs in `agente` (the status PATCH is agent/admin-only), fetches forwardings via `GET /forwardings`, and advances a deterministic subset through their lifecycle via `PATCH /forwardings/{id}/status` (body `{"status": ...}`): roughly leave ~⅓ at `aguardando_solucao`, move ~⅓ to `solucao_em_andamento`, and ~⅓ to `finalizado`, so the UI shows all three states. Use a fixed `--seed`. Idempotency: skip forwardings already past `aguardando_solucao` unless `--force`. Print a per-state count summary. **Note in the script docstring** that this models "resolution" at the forwarding level — `ReportStatus.resolvido` has no API transition (see plan Findings).
- **Files**: `scripts/seed_forwarding_lifecycle.py` (create)
- **References**: `product-design/project/standards.md § Backend`; status API in `src/fala_gavea/presentation/api/routers/forwardings.py` (`PATCH /{id}/status`, `_agent_or_admin`); valid values from `ForwardingStatus` (`src/fala_gavea/domain/entities/forwarding.py`: `aguardando_solucao`/`solucao_em_andamento`/`finalizado`).
- **Depends on**: requires forwardings to exist at runtime (seed_forwardings) — no code dependency on other plan steps.
- **Interface**: `main()` CLI: `--url`, `--seed`, `--force`.
- **Verify**: run the script; `GET /forwardings?status=finalizado` returns ≥1. Re-run skips already-advanced forwardings.
- **Tests**: N/A — live-API seed tooling.

### Step 6: Wire new phases + add `--profile` to seed_all.py
Extend the orchestrator:
- Add `--profile {showcase,full}` (default `showcase`). When `--profile showcase` and no explicit `--csv`, default the CSV to `data/seed_relatos_fala_gavea_200.csv` (small/curated/fast); `full` keeps `seed_relatos_fala_gavea_5k.csv`.
- Keep existing phases 1–5 (users, report types, relatos, forwardings, citizen01), then **append new phases in dependency order**: (6) Votes → `seed_votes.py`, (7) Comments → `seed_comments.py`, (8) Saved filters → `seed_saved_filters.py`, (9) Forwarding lifecycle → `seed_forwarding_lifecycle.py`. All inherit `--url`. Lifecycle should run after forwardings exist; votes/comments after relatos+forwardings.
- Add per-phase skip flags consistent with the existing style: `--skip-votes`, `--skip-comments`, `--skip-saved-filters`, `--skip-lifecycle`.
- Update the closing summary to list the new feature data and a short "Verify showcase features" checklist (votes visible on a relato dialog, comments on a forwarding, saved filters in the filter UI, a `finalizado` forwarding).
- **Files**: `scripts/seed_all.py` (modify)
- **References**: `product-design/project/standards.md § Backend`
- **Depends on**: Step 1, Step 2, Step 3, Step 4, Step 5
- **Interface**: `main()` CLI gains `--profile`, `--skip-votes`, `--skip-comments`, `--skip-saved-filters`, `--skip-lifecycle`.
- **Verify**: `uv run python scripts/seed_all.py --url http://localhost:8000` (default showcase) runs all 9 phases to completion against a freshly-started API and prints the new checklist. `--profile full` uses the 5k CSV.
- **Tests**: N/A — orchestrator over live-API scripts.

### Step 7: Add `make seed` target + docs
Add a `seed` target to the `Makefile` that accepts `URL` (default `http://localhost:8000`) and optional `PROFILE` (default `showcase`), invoking `uv run python scripts/seed_all.py --url $(URL) --profile $(PROFILE)`. Add it to `.PHONY` and to the `help` output (e.g. `seed  — seed the running app via API (override URL=... PROFILE=showcase|full)`). Document the new command and the showcase profile in `CLAUDE.md` (fala-gavea) under Build & Run, near the existing `seed_all.py` lines, including the new account list and that votes/comments/saved-filters/lifecycle are now seeded. Example invocation to document: `make seed URL=http://localhost:8000`.
- **Files**: `Makefile` (modify), `CLAUDE.md` (modify)
- **References**: existing `Makefile` target/`help` style; `CLAUDE.md § Build & Run`
- **Depends on**: Step 6
- **Verify**: `make seed URL=http://localhost:8000` (API running) executes the full showcase pipeline; `make help` lists `seed`. `make seed URL=http://localhost:8000 PROFILE=full` selects the 5k CSV.
- **Docs**: `CLAUDE.md` Build & Run section updated with `make seed` and new phases.
- **Tests**: N/A — build/docs change.

## Suggestions — additional seed entries (out of scope, for later)

Per the brief's request for *suggestions of new seed pipeline entries* beyond what's planned above:

1. **Anonymous reports + claim tokens.** The anonymous-report flow (roadmap-000151, plan-000158) stores a claim token in `localStorage`; no seed exercises it. A `seed_anonymous.py` could create a handful of anonymous relatos and print their claim tokens for manual "Meus relatos (anônimo)" testing.
2. **AI report-type suggestion provenance.** Once plan-000174 (pluggable report-type suggestion) lands, seed some relatos with `report_type_id = NULL` so the AI-suggestion + `ai_source` provenance UI has subjects to act on.
3. **`em_analise` reports.** Like `resolvido`, `em_analise` appears in the enum/LLM filter but has no observed API transition — if/when a triage endpoint is added, seed a few so all four report statuses are represented.
4. **A true report-level `resolvido` path.** Decide whether `resolvido` should be reachable (new endpoint or cascade from forwarding `finalizado`); today it's dead enum surface. Worth a `/research` or design decision before seeding it.
5. **Self-docs / help-chat smoke.** Not data-seed but pipeline-adjacent: a `make` convenience to force `reindex_selfdocs.py` so the platform-helper RAG (D-014/D-017) has a populated collection in a fresh local DB.

## Review (light)

- **Depth:** auto=light (tooling/scripts only, no production runtime code, ~8 files, low blast radius), floor=light, flag=none → **effective=light**.
- **API-only convention** upheld — all new scripts mutate via REST (CONVENTION_1). ✅
- **Rate-limit / self-vote** edge cases explicitly handled in Step 2 (429 backoff, 409 skip) — the most likely failure mode. ✅
- **Idempotency** specified per script so `make seed` is safely re-runnable. ✅
- **Resolved-status finding** surfaced rather than silently faked via a DB write. ✅
- **Risk:** votes density vs the 20/min limit on a larger `full` profile — mitigated by backoff + the showcase default; if `full` seeding of votes proves slow, a future option is an env-gated limiter bypass for seeding.

## Brief Traceability

- "makefile entry receiving url as parameter" → Step 7 (`make seed URL=...`).
- "initial seed … to showcase features" → Step 6 (`--profile showcase`, curated 200-row base + all feature phases).
- "features that do not have any seed, like upvotes" → Steps 2–5 (votes, comments, saved filters, forwarding lifecycle) + Step 1 (voter accounts).
- "check recent reflection … suggestions of new seed pipeline entries" → Gap analysis (reflection-000163) + Suggestions section.

## Implementation Summary (2026-06-26, manual mode)

All 7 steps implemented. Tooling-only — no `src/`/`tests/` changes; Tests N/A per plan.

| Step | Result | Notes |
|---|---|---|
| 1. Extra citizens | ✅ | `seed_users.py` now seeds citizen02–05 (+ docstring); idempotent via existing 409-skip. |
| 2. `seed_votes.py` | ✅ | Voter pool (citizen01–05 + agente); weighted 70/15/15 up/down/skip; **409 self-vote skip** + **429 backoff** (2→4→8s). |
| 3. `seed_comments.py` | ✅ | Curated pt-BR comment bank; 1–3 comments on first ~6 forwardings; skips forwardings that already have comments. |
| 4. `seed_saved_filters.py` | ✅ | 3 presets/user (Urgência alta, Pendentes de iluminação, Encaminhados recentes); skips existing names. |
| 5. `seed_forwarding_lifecycle.py` | ✅ | Advances ~⅓/⅓/⅓ to aguardando/solucao_em_andamento/finalizado via PATCH; documents the `resolvido` finding. |
| 6. `seed_all.py` | ✅ | `--profile {showcase,full}` (showcase=200 CSV default), phases 6–9 wired, `--skip-*` flags, updated summary. |
| 7. `make seed` + docs | ✅ | `make seed URL=... PROFILE=...`, `.PHONY` + `help` updated, `CLAUDE.md § Build & Run` documented. |

**Quality gate:** `py_compile` OK · `ruff check` clean · `pyright` 0 errors · `pytest` 308 passed.

**Not exercised here:** the live end-to-end seed run (`make seed`) needs a running API + Ollama; the plan's per-step `Verify` (vote counts, comments, saved filters, `finalizado` forwardings visible in the UI) should be run against a local server. Filed as a manual verification follow-up.
