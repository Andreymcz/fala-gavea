# Plan 000131 | REDESIGN-F | 2026-06-21 17:15 | Refine data exploration search filters | Review: standard
plan_format_version: 1

source: research-000129 -- staged filter + Apply, Tipos routing bug, date presets, table sort/full-text, map filter-this-area

## User brief

Implement research-000129 recommendations to refine the data-exploration workspace filters (citizen + agent journeys):

- **R1 (D-009)**: full staged filter model with an explicit **Aplicar** button. Add a `draftFilters` slice alongside committed `filters` in `workspaceStore`; the FilterPanel edits the draft; Apply commits draft -> filters so views re-fetch only on Apply; a "filtros alterados" dirty indicator; active-filter chips summarizing committed filters with per-chip remove; keep "Limpar". Map-drawn bbox and table "Similares" commit immediately (direct manipulation); only panel fields are staged. Wire aria-live for dirty/chips.
- **R2**: fix the Tipos combobox routing bug (the SPA catch-all swallows slashless `GET /report_types` and returns `index.html` in the built/served SPA) by guarding the catch-all against known API prefixes and aligning `api.ts` to canonical trailing-slash collection routes; same latent fix for `GET /forwardings`.
- **R3**: relative date presets (Hoje, Ultimos 7/15/30 dias, Este mes, Personalizado) computing since/until, revealing native date inputs only for Personalizado, showing resolved absolute dates.
- **R4**: TableView client-side column sorting + full-text reader (dialog with focus management or expandable row).
- **R5**: replace/augment the MapView two-click draw with a "Filtrar nesta area" button that sets bbox to `map.getBounds()`; keep "Limpar area"; optional live Rectangle feedback if draw retained.
- **R6**: regression tests (backend: slashless `GET /report_types` does not return HTML; frontend: `useReportTypes` populates the combobox).

## Agent interpretation

A frontend-led REDESIGN with one backend routing fix. The architectural core is R1: split the single Zustand `filters` object into a **committed** slice (read by all views via `useFilteredReports`/`useKeywords`) and a **draft** slice (edited by the FilterPanel), committed atomically by an Apply action. Because the semantic query becomes part of the draft, it only fires on Apply -- the un-debounced per-keystroke search problem dissolves without adding a debounce. Direct-manipulation inputs (map bbox, table "Similares" seed) bypass the draft and commit immediately so the map and table stay responsive. R2 is an independent, shippable bug fix. R3/R4/R5 are self-contained view/panel improvements that depend only on the store shape from R1 (R3) or nothing (R4, R5, R2).

This plan implements decision **D-009** (`product-design-as-intended.md`).

## Dependencies

**plan-000132 (unified `POST /reports/query` API — Phase B):**

- The FilterPanel and workspace views in this plan now read through `POST /reports/query` introduced by plan-000132, rather than calling separate `/reports` and `/reports/search` endpoints.
- The `useFilteredReports` and `useSemanticSearch` hooks are retargeted in **plan-000132 Step 7** to call `POST /reports/query` with the unified parameter envelope; the store shape and Apply semantics defined here remain unchanged.
- The R2 catch-all guard (`/report_types`, `/forwardings`) is an independent backend routing fix and remains valid regardless of the query API changes introduced by plan-000132.

## Files

- `frontend/src/store/workspaceStore.ts` (modify) + `workspaceStore.test.ts` (modify)
- `frontend/src/features/workspace/FilterPanel.tsx` (modify) + `FilterPanel.test.tsx` (modify)
- `frontend/src/features/workspace/DateRangePresets.tsx` (create) + test (create)
- `frontend/src/features/workspace/ActiveFilterChips.tsx` (create)
- `frontend/src/features/workspace/views/MapView.tsx` (modify)
- `frontend/src/features/workspace/views/TableView.tsx` (modify) + `TableView.test.tsx` (modify)
- `frontend/src/lib/api.ts` (modify) + `api.test.ts` (modify)
- `frontend/src/lib/types.ts` (modify -- DatePreset type if needed)
- `src/fala_gavea/presentation/api/main.py` (modify -- SPA catch-all guard)
- `tests/test_spa_fallback.py` (create -- backend regression)

## Decisions captured

- **D-009** (already recorded): staged draft+Apply filter model supersedes D-008 live cross-filtering.

---

## Steps

### Step 1: Split workspaceStore into committed + draft filter slices
Refactor `frontend/src/store/workspaceStore.ts` so panel filters are staged. Keep the existing committed `filters: WorkspaceFilters` (read by all views). Add `draftFilters: WorkspaceFilters` (initialized equal to `filters`, i.e. `{}`). Add/adjust actions:
- `setDraftFilter(patch: Partial<WorkspaceFilters>)` -- merges into `draftFilters` only (does NOT touch committed `filters`).
- `applyFilters()` -- commits: `filters = { ...draftFilters }`.
- `clearFilters()` -- resets BOTH: `filters = {}`, `draftFilters = {}`.
- `removeFilter(key: keyof WorkspaceFilters)` -- removes `key` from BOTH `filters` and `draftFilters` immediately (used by chip remove); recompute objects without that key.
- `setBbox(bbox)` -- direct manipulation: set `bbox` on BOTH `filters` and `draftFilters` immediately (map area applies now and stays in sync so it never appears as a pending diff).
- Repoint `setSemanticQuery(q)` to write to the draft (`setDraftFilter({ semanticQuery: q })`) so the semantic query is staged and only fires on Apply.
- Add a pure helper `filtersAreEqual(a: WorkspaceFilters, b: WorkspaceFilters): boolean` (compare the known keys: urgency, status, type_id, since, until, bbox, semanticQuery) and expose `isDirty(): boolean` returning `!filtersAreEqual(get().draftFilters, get().filters)`.
- Keep `structuredFilters()` reading committed `filters` (unchanged behavior). Retain `setFilter` as a thin alias to `setDraftFilter` ONLY if needed for back-compat; otherwise remove it and update callers (none outside FilterPanel/tests use it -- verified via grep).
Consumers `useFilteredReports` and `useKeywords` continue reading committed `filters` -- no change to them. The result: views re-fetch only when `applyFilters` runs, except bbox which commits immediately.
- **Files**: `frontend/src/store/workspaceStore.ts` (modify), `frontend/src/store/workspaceStore.test.ts` (modify)
- **References**: `project/standards.md § Frontend`
- **Interface**: store exposes `filters`, `draftFilters`, `setDraftFilter(patch)`, `applyFilters()`, `clearFilters()`, `removeFilter(key)`, `setBbox(bbox)`, `setSemanticQuery(q)`, `isDirty()`, `structuredFilters()`.
- **Verify**: `cd frontend && npm run test` passes; `npx tsc --noEmit` clean.
- **Tests**: Update `workspaceStore.test.ts`: setDraftFilter changes draft but not committed; applyFilters copies draft to committed; isDirty true after setDraftFilter and false after applyFilters/clearFilters; setBbox updates both slices and leaves isDirty false; removeFilter drops the key from both slices.

### Step 2: FilterPanel staged UI -- Apply button, dirty indicator, active-filter chips
Rework `frontend/src/features/workspace/FilterPanel.tsx` to read `draftFilters` for all input values and write via `setDraftFilter`. Add:
- An **Aplicar** primary button (calls `applyFilters`), disabled when `!isDirty()`; keep **Limpar** (calls `clearFilters`).
- A dirty indicator: when `isDirty()`, show "Filtros alterados -- clique Aplicar" in an `aria-live="polite"` region so screen readers announce the pending state.
- Active-filter **chips** rendered from committed `filters` (new component `ActiveFilterChips.tsx`): one chip per active committed filter (Tipo: <name>, Urgencia: <label>, Status: <label>, De/Ate/periodo, Area do mapa, Busca: "<q>") with an X that calls `removeFilter(key)`. Wrap chip add/remove in an `aria-live="polite"` region. Resolve type_id -> name via `useReportTypes`.
- The live count (`useFilteredReports().count`) continues to reflect committed results.
Move the semantic-search input to write to the draft (already routed via `setSemanticQuery` -> draft in Step 1). Pressing Enter in any text input should also trigger `applyFilters`.
- **Files**: `frontend/src/features/workspace/FilterPanel.tsx` (modify), `frontend/src/features/workspace/ActiveFilterChips.tsx` (create), `frontend/src/features/workspace/FilterPanel.test.tsx` (modify)
- **References**: `project/standards.md § Frontend`, `general/review-perspectives/a11y.md`
- **Depends on**: Step 1
- **Verify**: editing a Select shows the dirty indicator and does NOT change results until Aplicar; clicking Aplicar updates the central views; a chip X removes that filter immediately; `npm run test` passes.
- **Tests**: Update `FilterPanel.test.tsx` with a richer mock store (draftFilters, isDirty, applyFilters, removeFilter): Aplicar disabled when not dirty; dirty indicator text appears when isDirty true; clicking Aplicar calls applyFilters; chips render from committed filters and X calls removeFilter.
- **Docs**: Update contextual help for the workspace filter panel (staged apply + chips).

### Step 3: Relative date-range presets
Create `frontend/src/features/workspace/DateRangePresets.tsx`: a labeled control (Select or segmented buttons) with options Hoje, Ultimos 7 dias, Ultimos 15 dias, Ultimos 30 dias, Este mes, Personalizado. Selecting a relative preset computes `since`/`until` as `YYYY-MM-DD` strings (local date; `until` = today, `since` = today minus N days; "Este mes" = first day of current month) and writes them via `setDraftFilter({ since, until })`. Below the control, show the resolved absolute range ("01/06/2026 - 21/06/2026") so the relative choice is unambiguous. "Personalizado" reveals the existing native `<input type="date">` De/Ate fields (kept for keyboard/locale safety) bound to the draft. Replace the two standalone De/Ate blocks in `FilterPanel.tsx` with this component. Infer the active preset from current draft since/until on render (fallback to Personalizado when they do not match a preset).
- **Files**: `frontend/src/features/workspace/DateRangePresets.tsx` (create), `frontend/src/features/workspace/DateRangePresets.test.tsx` (create), `frontend/src/features/workspace/FilterPanel.tsx` (modify)
- **References**: `project/standards.md § Frontend`
- **Depends on**: Step 1, Step 2
- **Verify**: choosing "Ultimos 15 dias" sets draft since/until to today-15..today and shows the resolved dates; Personalizado reveals the date inputs; `npm run test` passes.
- **Tests**: `DateRangePresets.test.tsx`: selecting "Ultimos 7 dias" calls setDraftFilter with since = today-7 and until = today (freeze time via `vi.setSystemTime`); selecting Personalizado renders both date inputs; resolved-range label reflects the computed dates.

### Step 4: Map "Filtrar nesta area" (visible-bounds filter) replacing the blind two-click draw
Rework `frontend/src/features/workspace/views/MapView.tsx`. Replace the two-click `BboxDrawHandler` flow with a single **"Filtrar nesta area"** button in the existing overlay that, on click, reads the current map bounds and commits them: format `${sw.lat},${sw.lng},${ne.lat},${ne.lng}` from `map.getBounds()` and call `setBbox(...)` (immediate commit per Step 1). Use a small inner component with `useMap()` to access the map instance (react-leaflet v4). Keep the **"Limpar area"** button (calls `setBbox(undefined)`), shown only when `currentBbox` is set. Give the active button an `aria-pressed`/labeled state and >=44px touch target (reuse existing classes). Remove the `drawing` state machine and `BboxDrawHandler`. (Optional, only if free-draw is explicitly retained later: a live `<Rectangle>` -- not in scope here; the visible-bounds button supersedes it and gives immediate, self-evident feedback.)
- **Files**: `frontend/src/features/workspace/views/MapView.tsx` (modify)
- **References**: `project/standards.md § Frontend > 4 Map Conventions`, `general/review-perspectives/a11y.md`
- **Depends on**: Step 1
- **Verify**: clicking "Filtrar nesta area" filters reports to the current viewport (markers outside drop out after refetch); panning then clicking again updates the area; "Limpar area" clears it; no console errors; `npm run test` passes.
- **Tests**: N/A (map-instance interaction is integration-level; covered by manual test plan). Keep existing MapView render path compiling.

### Step 5: TableView column sorting + full-text reader
Enhance `frontend/src/features/workspace/views/TableView.tsx`:
- **Sorting**: make Texto, Tipo, Urgencia, Status, Data column headers clickable buttons that toggle asc/desc client-side over the `features` array (local `useState` for `{ key, dir }`). Urgencia sorts by severity order (alta > media > baixa), Data by `created_at` timestamp, others lexicographically (Tipo by resolved type name). Show a sort caret on the active column and set `aria-sort` on the `<th>`.
- **Full text**: stop relying solely on the 80-char truncation. Add a way to read the full report text -- a Dialog (`@/components/ui/dialog`, already present) opened by a "Ver" affordance on the row (or making the Texto cell a button), showing full `text`, type, urgency, status, date. Manage focus per Radix Dialog defaults (focus in on open, return to trigger on close, Esc closes). Keep row-selection checkbox behavior intact and ensure the new control `stopPropagation` so it does not toggle selection.
- **Files**: `frontend/src/features/workspace/views/TableView.tsx` (modify), `frontend/src/features/workspace/views/TableView.test.tsx` (modify)
- **References**: `project/standards.md § Frontend`, `general/review-perspectives/a11y.md`
- **Depends on**: none (reads `useFilteredReports` features)
- **Verify**: clicking a header sorts rows and flips on second click with `aria-sort` updating; opening the full-text dialog shows the complete relato and Esc closes it returning focus; selection still works; `npm run test` passes.
- **Tests**: Update `TableView.test.tsx`: clicking the Data header reorders rows; clicking Texto/"Ver" opens a dialog containing the full (non-truncated) text; the full-text control does not toggle row selection.

### Step 6: Guard the SPA catch-all against API prefixes (backend R2 fix)
In `src/fala_gavea/presentation/api/main.py`, prevent the SPA fallback from shadowing API routes. Define a module-level `API_PREFIXES = {"auth", "nl", "reports", "report_types", "forwardings", "admin", "health"}` (the prefixes registered in `create_app`). In `spa_fallback`, if the first path segment of `full_path` is in `API_PREFIXES`, return `JSONResponse({"detail": "Not Found"}, status_code=404)` instead of `index.html`. This makes any slashless/mismatched API request return an honest JSON 404 rather than silently serving HTML (the root cause that made the Tipos bug invisible: `res.json()` parsing `index.html`). Existing canonical routes (`/report_types/`, `/forwardings/`) are matched by their routers before the catch-all and are unaffected. Keep the file/`index.html` serving for all non-API paths.
- **Files**: `src/fala_gavea/presentation/api/main.py` (modify), `tests/test_spa_fallback.py` (create)
- **References**: `project/standards.md § Backend`, `general/review-perspectives/api.md`
- **Verify**: `uv run pytest tests/test_spa_fallback.py` passes; `uv run ruff check src/ tests/` clean; `uv run pyright src/` clean.
- **Tests**: `tests/test_spa_fallback.py` -- build an app with a temporary `static/` dir containing a sentinel `index.html`; assert `GET /report_types` (slashless) returns 404 JSON (NOT 200 `text/html` with the sentinel); assert `GET /report_types/` returns 200 JSON list; assert a non-API path (e.g. `/login`) still serves the SPA `index.html`.

### Step 7: Align frontend collection calls to canonical routes + combobox regression test (R2 + R6)
In `frontend/src/lib/api.ts`, change collection-root calls to the canonical trailing-slash form so they match the FastAPI routers directly and never reach the catch-all: `getReportTypes` -> `GET /report_types/`; `getForwardings` -> `GET /forwardings/`. (Sub-resource routes like `/reports/geojson` are unaffected.) This is the fix that makes the Tipos combobox actually populate in the served SPA, and pre-empts the same latent failure for the agent forwardings list.
- **Files**: `frontend/src/lib/api.ts` (modify), `frontend/src/lib/api.test.ts` (modify)
- **References**: `project/standards.md § Frontend`
- **Depends on**: Step 6
- **Verify**: `cd frontend && npm run test` passes; built SPA shows report types in the Tipo dropdown when types exist.
- **Tests**: Update `api.test.ts` (mock `fetch`): `getReportTypes()` requests a URL ending in `/report_types/` and returns the parsed array; `getForwardings()` requests `/forwardings/`. (Combined with Step 6's backend test, this is the R6 regression coverage: a slashless drift now fails loudly server-side and the client uses the canonical route.)

---

## Review Log (standard depth)

Perspectives selected via `review-perspectives-index.md`. The five recommendations were also evaluated by the research-reviewer across UX/ARCH/PERF/A11Y/TEST/API/MICRO at research-000129; findings are carried forward here.

| Perspective | Status | Note |
|-------------|--------|------|
| ARCH | Adopted | Draft/committed split keeps a single source of truth per slice; views read committed only; bbox/seed bypass draft as direct manipulation. Documented interface in Step 1 prevents consumer drift. |
| API | Adopted | Step 6 fixes the route-boundary defect at its root (catch-all no longer shadows API prefixes); Step 7 aligns the client to canonical routes. Latent `/forwardings` case covered. |
| PERF | Adopted | Staging removes the per-keystroke semantic search (it now fires only on Apply); geojson refetch batched to Apply. No debounce needed. |
| UX | Adopted | Apply + chips + dirty indicator give explicit control and clear "what is active". Diverges from D-008 live model -- intentional per D-009. Date presets reduce calendar friction; map "filter this area" is self-explaining. |
| A11Y | Adopted | aria-live for dirty indicator and chips (P0 dynamic-update announcements); Dialog focus management for full text; map button replaces a keyboard-inaccessible two-click gesture; native date inputs retained for Personalizado. aria-sort on sortable headers. |
| TEST | Adopted | Store, panel, presets, table, api, and SPA-fallback all carry tests; Step 6+7 add the regression coverage that was missing when the bug shipped. |
| MICRO | Adopted | Sort carets, chip remove affordances, immediate map-area feedback. |
| DX | Adopted | Step 1 publishes the store interface; small focused components (DateRangePresets, ActiveFilterChips). |
| SEC / DB / DATA / OPS / COMPAT / I18N / VIS / RESP | N/A | No auth/schema/PII/deploy/contract/locale/visual-token/breakpoint changes; UI strings are pt-BR inline per existing convention. |

**Deferred / out of scope**: live `<Rectangle>` free-draw (superseded by visible-bounds button); saved-filter and NL-to-query-params features (the user logged a separate research brief for those -- not part of this plan).

## Test plan (manual)

1. As citizen: open workspace; edit Tipo/Urgencia/Status -> results do NOT change, "Filtros alterados" appears -> click Aplicar -> Mapa+Tabela update; chips show the active filters; click a chip X -> that filter clears immediately.
2. Date presets: pick "Ultimos 15 dias" -> resolved dates shown, Aplicar -> results narrow; Personalizado -> date inputs appear.
3. Tipos combobox: with report types seeded, the Tipo dropdown lists them (served SPA build, not just dev).
4. Table: click headers to sort (incl. Data, Urgencia); open a relato's full text in the dialog and close with Esc.
5. Map: pan/zoom to an area -> "Filtrar nesta area" -> only in-view reports remain; "Limpar area" resets.
6. As agent: Forwardings list still loads (canonical route).

## Manual actions after implementation

- Rebuild the SPA so the served `static/` reflects the changes: `cd frontend && npm run build`. (Dev mode `npm run dev` proxies and does not exercise the catch-all bug.)
- Restart the API only if running the built SPA: `uv run uvicorn fala_gavea.presentation.api.main:app`.
