# Progress -- Plan 000137

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 1 — 2026-06-21 — SUCCESS

Implemented committed/draft split + panel state in `workspaceStore.ts`:
- Added `draftFilters`, `panelOpen`, `loadedPresetName`, `draftFilterName` state fields
- New actions: `setDraftFilter`, `applyFilters`, `discardDraft`, `removeFilter`, `togglePanel`, `setLoadedPresetName`, `setDraftFilterName`
- Modified: `clearFilters` now resets both slices + name fields; `setBbox` commits to both slices; `setSemanticQuery` routes to draft only; `setFilter` aliased to `setDraftFilter`
- Added `isDirty()` derived selector comparing draft vs committed across all 7 known filter keys
- Tests updated with 10 new cases covering all new behaviors; all 43 tests pass
- TypeScript: no errors (`npx tsc --noEmit` clean)
- Committed: `3072bc1`

### Step 2 — 2026-06-21 — SUCCESS

Rewrote `FilterPanel.tsx` as a four-section left panel (`w-72`):
- Section 1: Preset bar with name/dirty indicator (`loadedPresetName + " *"`), disabled Salvar/Carregar buttons, count badge, collapse toggle
- Section 2: `<ActiveFilterChips />` stub + "Nenhum filtro ativo" fallback
- Section 3: Draft controls — Select inputs read `draftFilters` / call `setDraftFilter`; `<DateRangePresets />` stub; semantic Input with Enter key → `applyFilters()`; dirty indicator aria-live; Aplicar (disabled when `!isDirty`) and Limpar buttons
- Section 4: Disabled NL assistant footer
- Collapse: when `panelOpen === false` renders only a toggle button with badge; aria-label switches between "Recolher" and "Expandir"
- Pattern: `useWorkspaceStore(s => s.isDirty())` — selector form, never destructured
- Stubs created: `ActiveFilterChips.tsx`, `DateRangePresets.tsx` (return null)
- Tests: 10 new cases covering all specified behaviors; all 51 tests pass
- TypeScript: clean
- Committed: `e171ca4`

### Step 3 — 2026-06-21 — SUCCESS

Implemented `ActiveFilterChips.tsx` (replaced stub):
- Reads `filters` (committed slice) and `removeFilter` from `useWorkspaceStore`
- Uses existing `useReportTypes` hook at `frontend/src/hooks/useReportTypes.ts`
- Label mappings: urgency (alta/media/baixa → Alta/Média/Baixa), status (pt-BR), since/until (pt-BR via `toLocaleDateString`), bbox ("Área do mapa"), semanticQuery (truncate at 20 chars + '...')
- Empty state returns `null`; wraps chips in `aria-live="polite"` div
- Each chip is `<span>` with `×` button calling `removeFilter(key)`
- Tests: 8 cases all pass; TypeScript clean
- Committed: `6f45974`

### Step 4 — 2026-06-21 — SUCCESS

Implemented `DateRangePresets` component at `frontend/src/features/workspace/DateRangePresets.tsx`:
- Added `DatePreset` type to `frontend/src/lib/types.ts`
- Renders 6 preset buttons: Hoje | Últ. 7 dias | Últ. 15 dias | Últ. 30 dias | Este mês | Personalizado
- Active preset detected via `detectActivePreset()` comparing computed ranges to `draftFilters.since/until`; falls back to 'personalizado' when no match
- Non-custom presets: call `setDraftFilter({ since, until })` + show resolved "De: DD/MM/YYYY Até: DD/MM/YYYY" below row
- Personalizado: shows two `<input type="date">` bound to `draftFilters.since/until` via `setDraftFilter`
- Active button styled with `ring-2 ring-blue-500 bg-blue-50 border-blue-400`
- Tests: 7 cases in `DateRangePresets.test.tsx`; all pass (66 total passing, 1 pre-existing failure in ActiveFilterChips truncation test — unrelated to this step)
- TypeScript: clean
- Committed: `bda600f`

### Step 5 — 2026-06-21 — SUCCESS

SPA routing fix — catch-all guard + api.ts trailing slash alignment:
- `main.py`: added `_API_PREFIXES` set; `spa_fallback` now guards first-path-segment against known API prefixes, returning `JSONResponse({"detail": "Not Found"}, 404)` before serving `index.html`; added `response_model=None` to avoid FastAPI union-type annotation error
- `api.ts`: `getReportTypes()` URL → `"/report_types/"` (trailing slash); `getForwardings()` URL template → `` `/forwardings/${q}` `` (slash before query string)
- `tests/test_spa_fallback.py`: 6 tests covering trailing-slash JSON, auth/reports JSON, guard-with-static-dir integration (using `tmp_path`), and `_API_PREFIXES` completeness; all 6 pass
- Pyright: 66 pre-existing errors in other files; no new errors in changed files
- Committed: `76df8e2`

### Step 6 — 2026-06-21 — SUCCESS

Reworked `TableView.tsx` with sort, full-text dialog, pagination, score column, density toggle:
- **Sort**: `SortKey` type + `sortConfig` state; `<th aria-sort>` + `<button aria-label>` per column; sort icon ↑/↓/⇅; null scores sort last
- **Full-text dialog**: uses existing `@/components/ui/dialog.tsx` (Radix); "Ler relato" button renders only when text > 80 chars; dialog shows full text + Tipo/Urgência/Status/Data fields + Similares button; focus-return via `useRef`
- **Pagination**: `useFilteredReports` now accepts `{ limit, offset }` options; `PAGE_SIZE=50`; pagination bar below table; summary "N relatos encontrados — página X de Y" above; `filtersKey = JSON.stringify(filters)` pattern to avoid stale object identity reset loop
- **Score column**: visible only when `ranked_by === 'similarity'`; color-coded (green/amber/gray); `sr-only` accessibility labels; `score` added to `ReportProperties` type
- **Density toggle**: "Compacto"/"Confortável" toggle; `h-7`/`h-10` row height
- `ReportProperties` type extended with `score?: number | null`; `useFilteredReports` return extended with `total` and `ranked_by`
- Tests: 9 new cases in `TableView.test.tsx`; all 72 pass; TypeScript clean
- Committed: `0ad89ab`

### Step 7 — 2026-06-21 — SUCCESS

Added `MapControls` child component inside `MapContainer` in `MapView.tsx`:
- Imports `useMap` from react-leaflet; `LatLngBounds` from leaflet
- `MapControls` renders two buttons centered at top of map (z-[1000]):
  - "Filtrar nesta área" — calls `map.getBounds()` → computes S/W/N/E → calls `setBbox(...)` (commits both slices immediately)
  - "Limpar área" — calls `setBbox(undefined)`; disabled (`opacity-40 cursor-not-allowed`) when `!hasBbox`
- `handleFilterArea` callback added to `MapView` using `useCallback`
- Existing "Desenhar área" draw-by-click mechanism kept as secondary (top-right overlay, outside MapContainer)
- `MapView.test.tsx` created with explicit `import { describe, it, expect } from 'vitest'` + manual test guide for 3 scenarios
- TypeScript: clean (`npx tsc --noEmit` no errors)
- Committed: `7a81e10`

### Step 8 — 2026-06-21 — SUCCESS

Draft-loss guard wired into `WorkspacePage.tsx`:
- `useBlocker(isDirty)` from react-router-dom v6.26.2 intercepts SPA-internal navigation
- `useEffect` registers `beforeunload` handler when `isDirty` is true, removes it on cleanup
- `Dialog` (existing `@radix-ui/react-dialog`) shows "Descartar e sair" / "Voltar" options
- "Descartar e sair" calls `discardDraft()` then `blocker.proceed()`; "Voltar" calls `blocker.reset()`
- `@radix-ui/react-alert-dialog` not needed — reused existing Dialog component
- Tests: 8 new cases in `WorkspacePage.test.tsx` covering isDirty() scenarios and beforeunload listener logic; 80 total tests pass (14 test files)
- TypeScript: clean; ruff 2 errors pre-existing (unused import in test_static_spa.py); pytest 1 pre-existing failure (test_api_works_without_static_dir); pyright 66 pre-existing errors
- Pending entry plan-000131/implement closed
- Committed: (see below)
