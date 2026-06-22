# Research 000145 | FEAT-X | 2026-06-22 19:47 UTC | Cesta de relatos + citizen transparency journeys

source: reflection-000144
spawned: roadmap-000146
tags: ux, frontend-architecture, semantic-search, api-design, security, transparency

## User brief (verbatim)

> cesta de relatos (agent journey) + citizen transparency journeys. Anchored on reflection-000144. AGENT: a "cesta de relatos" (basket of reports) as a first-class component peer to map/table — agent adds reports to the basket without leaving the interface, a top-right icon shows the basket count; in the basket the agent checks whether the selected set has SIMILAR reports still in status=aberto, reviews the reports, and creates the encaminhamento there. How does this relate to / replace the existing Zustand selection store + SelectionBar + CreateForwardingDialog (plan-000104)? How to compute set-similarity for OPEN reports given only per-report GET /reports/{id}/similar exists? CITIZEN: login + create relato by clicking the map with an inline form on the main page (no separate page); see list of relatos; see list of encaminhamentos; see which encaminhamentos are linked to which relatos. Note the gap: plan-000079 forwarding endpoints are all gated agent+admin — citizen has no public read surface for encaminhamentos.

## Agent interpretation

Two journeys, both building on infrastructure that already exists rather than greenfield work:

1. **Agent "cesta de relatos"** — elevate the existing `workspaceStore.selectedIds` selection into a first-class basket: a top-right count badge plus a dedicated basket *view* (peer to map/table) where the agent reviews the set, sees similar **open** reports, and creates the encaminhamento. The floating `SelectionBar` is replaced. The new technical piece is *set-similarity* (centroid over the selected reports' embeddings), since today only per-report `similar()` exists.

2. **Citizen transparency** — inline relato creation by clicking the main-page map (no `/report` page round-trip), a relatos list with an optional "meus relatos" filter, and a **public** read surface for encaminhamentos including the relato↔encaminhamento links. The backend gap is real: all `/forwardings` routes require agent+admin.

### Design decisions taken with the user (this session)

| # | Decision | Value chosen |
|---|----------|--------------|
| 1 | "relato aberto" maps to which `ReportStatus` | **Only `pendente`** |
| 2 | Who reads encaminhamentos + links | **Fully public (no login)** |
| 3 | Citizen "list of relatos" scope | **All relatos + a "meus relatos" filter** |
| 4 | Basket vs existing SelectionBar/selectedIds | **Elevate `selectedIds` into the cesta** (replace floating bar) |

## Files reviewed

- `src/fala_gavea/presentation/api/routers/forwardings.py` — all 5 endpoints gated `require_any_role("agent","admin")`
- `src/fala_gavea/presentation/api/routers/reports.py` — POST/query/keywords/{id} require auth; geojson/search/{id}/similar are public
- `src/fala_gavea/domain/entities/report.py` — `ReportStatus = pendente | em_analise | encaminhado | resolvido` (no `aberto`)
- `src/fala_gavea/domain/repositories/report_repository.py` — `ReportFilters` has no `author_id`
- `src/fala_gavea/domain/repositories/semantic_ports.py` — `ISemanticSearchPort.{search,similar,rank}`
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` — `get(ids, include=["embeddings"])` available; status NOT in Chroma metadata
- `src/fala_gavea/application/use_cases/reports/find_similar_reports.py` — per-report similarity use case
- `frontend/src/store/workspaceStore.ts` — `selectedIds: Set<string>`, `toggleSelect`, `clearSelection`, `ViewId = 'map'|'table'|'keywords'|'similars'|'chat'`
- `frontend/src/features/map/SelectionBar.tsx`, `CreateForwardingDialog.tsx` — floating bar + create dialog (agents only)
- `frontend/src/features/workspace/WorkspacePage.tsx`, `views/MapView.tsx`, `views/TableView.tsx` — view grid; map-click consumed by bbox-draw; table rows have selection checkboxes
- `frontend/src/features/report/ReportFormPage.tsx` — separate `/report` page with manual lat/lon + geolocate
- `frontend/src/features/forwardings/ForwardingsPage.tsx`, `App.tsx`, `components/layout/Header.tsx` — routing + nav

---

## Q&A log

### Q1 (verbatim)

> cesta de relatos (agent journey) + citizen transparency journeys. Anchored on reflection-000144. [...full brief above...]

**Answer.**

#### Finding: most of this is presentation work on existing plumbing

- The **basket already exists as state**: `selectedIds` is fed from *both* the map (`ReportMarkers.onToggleSelect`) and the table (row checkbox → `toggleSelect`, `TableView.tsx:262`). research-000092 step 6 flagged "seleção presa só ao mapa" — that is already solved. What's missing is the *first-class surface* (badge + dedicated view) and the *similar-open* check.
- **Citizen create** already works at the API level: `POST /reports/` only needs `get_current_user` (any role). The gap is purely UX — it lives on a separate `/report` page instead of an inline map-click form.
- **Citizen relatos list** already works: the public table/map render all reports. The only addition is an author filter for "meus relatos".
- **Citizen encaminhamento read is the one true backend gap**: every `/forwardings` route is agent+admin, and there is no report→forwarding reverse lookup.

#### A — Agent: cesta de relatos (Decision 4: elevate `selectedIds`)

- **Backing store**: keep `selectedIds` as the single source of truth. No second selection model. Rename the user-facing concept to "cesta"; the store key can stay `selectedIds` (or alias `basket`).
- **Top-right badge**: add a basket button with count to `Header.tsx` (visible to agent/admin), reading `useWorkspaceStore(s => s.selectedIds.size)`. Clicking it activates the basket view (and opens the panel if collapsed).
- **Basket as a view**: add `'cesta'` to the `ViewId` union, to `ViewToggleBar`, and to the `WorkspacePage` render switch. The basket view: lists selected reports (hydrate from the `useFilteredReports` cache, fall back to fetch-by-id for items scrolled out of the current filter), supports per-item remove, embeds the **similar-open** panel (E), and hosts `CreateForwardingDialog` inline (review → create in one place).
- **Replace the floating SelectionBar**: remove `SelectionBar` from `WorkspacePage`; its "Criar encaminhamento" action moves into the basket view. (Optional: keep a minimal "ver cesta (N)" affordance, but Decision 4 chose replacement.)
- **No DB/schema change** — the basket is frontend state; creation still goes through the existing `POST /forwardings/`.

#### B — Citizen: inline relato creation by map click (no separate page)

- **Mode arming (the key UX problem)**: a single map click is currently consumed by `BboxDrawHandler` for bbox drawing. A click cannot silently mean "filter area", "select marker", *and* "create report". Resolve with an explicit **"Adicionar relato aqui"** mode button (mirrors the existing "Desenhar área" arm/disarm pattern in `MapView.tsx:150`). Armed → next map click drops a provisional marker and opens an inline form (Radix Dialog or a right-side panel) with `lat`/`lon` prefilled from the click.
- **Reuse the form**: extract `ReportFormPage`'s field/validation logic into a shared `ReportFormFields` component (or `useReportForm` hook) used by both the inline dialog and the existing `/report` route. Keep `geolocate` as an alternative inside the inline form.
- **Auth**: arming the mode while anonymous prompts login (reuse `RequireAuth` semantics or a toast+redirect). Creation needs a logged-in user (`POST /reports/` requires `get_current_user`).
- **Fate of `/report`**: keep the route as a deep-link/fallback but make map-click the primary path; the Header "Novo relato" link can arm the map mode instead of navigating.

#### C — Citizen: relatos list + "meus relatos" filter (Decision 3: both)

- The public list already exists (table/map). Add an **author filter**:
  - Domain: add `author_id: str | None` to `ReportFilters`.
  - API: add `author_id` to `ReportFiltersQuery` (geojson) and `ReportQueryRequest` (POST /query).
  - Repo: thread `author_id` through `find_all` / `find_page` in the SQLAlchemy report repo (add `WHERE author_id = ?`); consider a DB index on `reports.author_id`.
  - Frontend: a "Meus relatos" toggle in `FilterPanel` that sets `author_id = currentUser.id` on the draft filters. Visible to any logged-in user.

#### D — Citizen: public encaminhamentos + relato↔encaminhamento links (Decision 2: fully public)

The one real backend build. Two sub-parts:

1. **Public read of encaminhamentos**. Add public read routes rather than relaxing the agent+admin ones in place, to keep write/manage gated and the public contract explicit:
   - `GET /forwardings/public` (list, optional `status` filter) and `GET /forwardings/public/{id}`.
   - Use a **public response schema** that omits `agent_id` (or replaces it with the agent's display name) — citizens don't need the internal user id. `institution`, `proposed_solution`, `status`, linked report summaries, timestamps are the transparency payload.
   - `POST`/`PATCH` stay `require_any_role("agent","admin")` (constitution T2: auth via `dependencies.py`; the public routes simply omit the role dependency).
2. **Reverse link report → forwardings**. Add `GET /reports/{id}/forwardings` (public) returning the encaminhamentos linked to a report. Needs a repo method (e.g. `find_forwardings_by_report_id`) querying the existing `ForwardingReportModel` join — no schema change.
3. **Frontend**: add an "Encaminhamentos" nav link for everyone (read-only `ForwardingsPage` variant when not agent); on report popups/table rows show a linked-encaminhamento badge ("Encaminhado → RioLuz · em andamento") sourced from `GET /reports/{id}/forwardings`.
4. **Privacy note (Decision 2 consequence)**: since `proposed_solution` becomes world-readable, it must be written as citizen-facing prose. No constitution invariant blocks this (S3 concerns LLM/semantic read-only; S2/C1 concern citizen DB/local-first, not forwarding visibility), but flag the copy-voice expectation to agents.

#### E — Agent: set-similarity over the basket, filtered to open reports

Today only `ISemanticSearchPort.similar(report_id, n)` exists (single seed). Two options:

- **(Recommended) Backend centroid endpoint.** Add `similar_to_set(report_ids: list[str], n: int) -> list[tuple[str,float]]` to `ISemanticSearchPort`, implemented in `ChromaSearchClient` by `get(ids, include=["embeddings"])` → average vectors into a centroid → `query(query_embeddings=[centroid], n_results=n+len(ids))` → drop the seed ids. New use case `FindSimilarToReportSet` hydrates hits from SQLite, **filters `status == pendente`** (Decision 1) and excludes basket ids. New route `POST /reports/similar-to-set` (agent+admin), body `{report_ids, n}`. One Chroma round-trip; matches T1 (semantic only via infrastructure) and T5 (DB via repo).
- **(Cheaper fallback) Client-side fan-out.** Call `GET /reports/{id}/similar` for each basket item, union + dedupe, exclude basket ids, and filter `status === "pendente"` client-side (the `ReportSearchResult` already carries `status`). No backend change, but N requests and a union-of-neighborhoods rather than a true centroid; quality degrades as the basket grows.

Recommendation: ship the **fan-out** as iteration 1 if speed matters, then the **centroid endpoint** as the durable version. Note that "open = only pendente" (Decision 1) means a relato already `em_analise`, `encaminhado`, or `resolvido` will not surface as a duplicate candidate.

#### Perspective synthesis

- **Architecture**: every recommendation respects T1/T2/T5 — new public forwarding routes still go through `dependencies.py` (just without `require_role`); set-similarity stays in `infrastructure/chromadb`; author filter stays in the repo. No clean-architecture violation.
- **Security/privacy**: the deliberate move from agent+admin to fully-public forwarding read is the main surface change; mitigations are the public schema (omit `agent_id`) and the citizen-facing `proposed_solution` copy expectation.
- **UX**: the map-click ambiguity (filter vs select vs create) is the highest-risk detail — explicit arm/disarm modes are required, not optional. The basket badge + dedicated view directly closes research-000092's "seleção presa só ao mapa" pain point.
- **Performance**: centroid set-similarity is one query vs N for fan-out; author filter wants a `reports.author_id` index.
- **Data model**: no schema changes anywhere — basket is client state, author filter uses an existing column, reverse-link uses the existing join table.

---

## Recommendations summary

1. **(HIGH)** Elevate `selectedIds` into a first-class "cesta": top-right count badge in `Header`, a new `'cesta'` view in `ViewId`/`ViewToggleBar`/`WorkspacePage`, remove the floating `SelectionBar`, embed review + `CreateForwardingDialog` in the basket view. No backend change.
2. **(HIGH)** Add public encaminhamento read: `GET /forwardings/public` + `GET /forwardings/public/{id}` with an `agent_id`-free public schema; keep POST/PATCH agent+admin. Add an "Encaminhamentos" nav link for all users.
3. **(HIGH)** Add report→forwarding reverse link: `GET /reports/{id}/forwardings` (public) + repo method over `ForwardingReportModel`; show a linked-encaminhamento badge on report popups/rows.
4. **(HIGH)** Inline citizen relato creation via map click: explicit "Adicionar relato aqui" arm mode in `MapView`, inline prefilled form (extract shared `ReportFormFields`/`useReportForm` from `ReportFormPage`), login prompt when anonymous; keep `/report` as fallback.
5. **(MEDIUM)** Set-similarity for the basket filtered to `pendente`: ship client-side fan-out first, then add `similar_to_set` centroid + `POST /reports/similar-to-set` (agent+admin) as the durable version.
6. **(MEDIUM)** "Meus relatos" filter: add `author_id` to `ReportFilters` + query schemas + SQLAlchemy repo (+ index), and a toggle in `FilterPanel`.
7. **(LOW)** Record decisions D-1..D-4 (open=pendente; public encaminhamento read; relatos all+mine; cesta=elevated selectedIds) as D-NNN entries via `/design` so they survive as design intent.
