# Roadmap 000146 | 2026-06-22 20:50 UTC | Cesta de relatos + citizen transparency journeys

source: research-000145

## Brief (verbatim)

Implement research-000145 (cesta de relatos + citizen transparency journeys) in dependency-aware waves. Agent + citizen transparency journeys; decisions D-010..D-013.

## Source
- _output/research-logs/research-000145-cesta-de-relatos-and-citizen-transparency-journeys.md (read)
- product-design/project/product-design-as-intended.md §Decisions D-010..D-013 (read)
- product-design/project/conventions.md (read)
- src/fala_gavea/presentation/api/routers/{forwardings,reports}.py (read)
- src/fala_gavea/domain/{entities/report.py, repositories/{report_repository,semantic_ports}.py} (read)
- src/fala_gavea/infrastructure/chromadb/chroma_search_client.py (read)
- frontend/src/store/workspaceStore.ts, features/{map,workspace,report,forwardings}/* (read)

## Decisions in force (from research-000145)
- **D-010** — "relato aberto" = `ReportStatus.pendente` only.
- **D-011** — encaminhamento read is fully public; new public GET routes with an `agent_id`-free schema; POST/PATCH stay agent+admin.
- **D-012** — citizen relatos list = all + a "meus relatos" filter (needs `author_id` plumbing).
- **D-013** — "cesta de relatos" elevates `selectedIds` (badge + dedicated view); the floating SelectionBar is removed.

## Context
All domain entities already exist (`Report`, `ReportType`, `Forwarding`, `ForwardingReport`, `User`). This roadmap is **additive** — no scaffold, no new tables. The agent selection store (`selectedIds`, fed by both map and table) and the multi-report forwarding cascade are already in place; the work is presentation, four new/extended read endpoints, and set-similarity.

## Wave Summary

### Wave 0 — Backend foundations (parallel; 4 independent items)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 1 | author-filter | Add `author_id` to ReportFilters + query schemas + SQLAlchemy repo (+ index) | backend | technical | plan-TBD | — | pending |
| 2 | public-forwarding-read | `GET /forwardings/public` + `/forwardings/public/{id}` with `agent_id`-free public schema; writes stay agent+admin | backend | technical | plan-TBD | — | pending |
| 3 | report-forwardings-reverse | `GET /reports/{id}/forwardings` (public) + repo method over `ForwardingReportModel` | backend | technical | plan-TBD | — | pending |
| 4 | set-similarity | `similar_to_set` on `ISemanticSearchPort`/`ChromaSearchClient` + `FindSimilarToReportSet` use case (filter `pendente`) + `POST /reports/similar-to-set` (agent+admin) | backend | technical | plan-TBD | — | pending |

**Item 1 — author-filter** (Rec 6): add `author_id: str | None` to `ReportFilters`; add `author_id` to `ReportFiltersQuery` (geojson) and `ReportQueryRequest` (POST /query); thread through SQLAlchemy `find_all`/`find_page` (`WHERE author_id = ?`); add a DB index on `reports.author_id`. Tests: filtering by author returns only that author's reports.

**Item 2 — public-forwarding-read** (Rec 2 / D-011): add `GET /forwardings/public` (optional `status` filter) and `GET /forwardings/public/{id}` with a `PublicForwardingResponse` schema that omits `agent_id` (institution, proposed_solution, status, linked report summaries, timestamps). `POST`/`PATCH` unchanged (agent+admin). Tests: anonymous client can read; agent_id absent from payload.

**Item 3 — report-forwardings-reverse** (Rec 3): add `GET /reports/{id}/forwardings` (public) returning encaminhamentos linked to a report; add a repo method (e.g. `find_forwardings_by_report_id`) querying the existing `ForwardingReportModel` join. Tests: returns the linked forwardings; empty list when none; 404 on unknown report.

**Item 4 — set-similarity** (Rec 5 backend / D-010): add `similar_to_set(report_ids, n)` to `ISemanticSearchPort`; implement in `ChromaSearchClient` via `get(ids, include=["embeddings"])` → centroid → `query(n + len(ids))` → drop seed ids; add `FindSimilarToReportSet` use case that hydrates from SQLite, filters `status == pendente`, excludes seed ids; add `POST /reports/similar-to-set` (agent+admin), body `{report_ids, n}`. Tests: centroid query returns neighbors; pendente-only; seeds excluded; 503 when search port unavailable.

### Wave 1 — Agent UX: cesta de relatos (1 item) — depends on Wave 0 #4

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 5 | cesta-de-relatos | Elevate `selectedIds` into a first-class basket: Header count badge + `'cesta'` view (review + remove + similar-open panel + inline CreateForwardingDialog); remove floating SelectionBar | frontend | design | plan-TBD | set-similarity | pending |

**Item 5** (Rec 1 + Rec 5 frontend / D-013): add `'cesta'` to `ViewId` in `workspaceStore.ts`, `ViewToggleBar`, and `WorkspacePage` render switch. Header gets a basket button with count (`selectedIds.size`, agent/admin). Basket view: lists selected reports (hydrate from `useFilteredReports` cache; fetch-by-id fallback), per-item remove, a "similares abertos" panel calling `POST /reports/similar-to-set` (client fan-out over `GET /reports/{id}/similar` as the fallback if the endpoint is unavailable), and an inline `CreateForwardingDialog`. Remove `SelectionBar` from `WorkspacePage`. Tests: basket view renders selection; remove works; create flow intact.

### Wave 2 — Citizen UX (2 items, parallel) — #7 depends on Wave 0 #1/#2/#3

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 6 | citizen-inline-create | Map-click "Adicionar relato aqui" arm mode + inline prefilled form (extract shared `ReportFormFields`/`useReportForm`); login prompt when anonymous; keep `/report` fallback | frontend | design | plan-TBD | — | pending |
| 7 | citizen-transparency-views | "Meus relatos" filter toggle + public "Encaminhamentos" nav/read-only page + linked-encaminhamento badge on report popups/rows | frontend | design | plan-TBD | author-filter, public-forwarding-read, report-forwardings-reverse | pending |

**Item 6** (Rec 4): add an "Adicionar relato aqui" arm mode to `MapView` (mirrors the "Desenhar área" arm/disarm pattern); armed → next map click drops a provisional marker and opens an inline form (Radix Dialog) with `lat`/`lon` prefilled. Extract `ReportFormPage`'s fields/validation into a shared `ReportFormFields` component (or `useReportForm` hook) reused by both the inline dialog and `/report`. Anonymous arming prompts login. Tests: armed click opens prefilled form; create succeeds; `/report` still works.

**Item 7** (Rec 2/3/6 frontend): "Meus relatos" toggle in `FilterPanel` (sets `author_id = currentUser.id`); "Encaminhamentos" nav link for all users + a read-only `ForwardingsPage` variant consuming `GET /forwardings/public`; linked-encaminhamento badge on report popups/table rows sourced from `GET /reports/{id}/forwardings`. Tests: meus-relatos filters to own; public list renders without login; badge shows linked status.

> The `Plan` column starts as `plan-TBD` for every row. Fill in the real ID **only after** `/plan` has been invoked for that work item and has returned the reserved ID.

## Execution Instructions

### Wave 0 (parallel — 4 backend plans)
Four independent backend changes; no inter-dependencies. Execute together or in any order. Run `uv run pytest` + `uv run ruff check src/ tests/` + `uv run pyright src/` before closing.

### Wave 1 (1 frontend plan)
Depends on Wave 0 #4 (`set-similarity`). Execute after Wave 0. Run `cd frontend && npm run test` + `npm run build`.

### Wave 2 (parallel — 2 frontend plans)
#6 has no backend dependency (can start anytime). #7 depends on Wave 0 #1/#2/#3. Execute after Wave 0 (and may run alongside Wave 1). Run frontend tests + build.

## Implementation directive (from user)
Implement each wave as it is planned, **with a clean (fresh, isolated) context at every implementation start** — each phase runs in its own cold agent context. Verify (tests + lint) between waves before proceeding to the next.
