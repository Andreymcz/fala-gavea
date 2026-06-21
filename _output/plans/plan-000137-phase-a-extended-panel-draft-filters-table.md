# DONE | 2026-06-21 22:02 UTC | Plan 000137 | REDESIGN-A | 2026-06-21 19:50 UTC | Phase A: extended panel, draft filters, table UX | Review: standard
plan_format_version: 1

source: research-000136 (left-panel layout, draft model, table UX), research-000129 (staged filter, chips, date presets, routing fix, table, map), plan-000131 (superseded by this plan — same scope extended)

## User brief

Phase A of the UI overhaul: build the four-section left panel (`w-72`, collapsible), the full staged draft/Apply model (with `loadedPresetName`, `draftFilterName`, and a draft-loss guard), date presets, active-filter chips, the SPA routing bug fix, a reworked TableView (column sort, Radix Dialog full-text, pagination, score column, density toggle), and the MapView "Filtrar nesta área" button. This plan supersedes plan-000131 (same items extended with the four-section layout from research-000136). Does NOT include saved filters (Phase B) or the NL filter parser (Phase C).

## Agent interpretation

A frontend-led REDESIGN with one backend fix. The architectural core is the Zustand store refactor (Step 1): split a single `filters` object into `filters` (committed, read by views) and `draftFilters` (edited by the panel), with a suite of new actions. The FilterPanel becomes the four-section left panel from research-000136 (Step 2). ActiveFilterChips and DateRangePresets are new self-contained components (Steps 3–4). The SPA catch-all routing fix (Step 5) resolves the confirmed production defect where `/report_types` and `/forwardings` return HTML. TableView gains sort, full-text dialog, pagination, and score column (Step 6). MapView replaces the broken two-click draw with a "Filtrar nesta área" button and optionally retains the draw with live Rectangle feedback (Step 7). Tests round out each step.

**Relationship to plan-000131:** this plan is a superset. Plan-000131 is formally superseded; its pending entry can be closed.

**Relationship to Phase B (saved filters) and Phase C (NL parser):** the store additions in Step 1 (`loadedPresetName`, `draftFilterName`, `panelOpen`) are stubs that Phase B and C will wire up. Section 1 (preset bar) and Section 4 (NL assistant) are scaffolded as visible placeholders in Step 2, ready for Phase B and C to fill.

## Dependencies

None outside this repo. `@radix-ui/react-dialog` and `@radix-ui/react-alert-dialog` are required; check `package.json` before Step 6 and install if absent. `@tanstack/react-table` is optional (sort can be implemented without it; see Step 6 note).

## Files

- `frontend/src/store/workspaceStore.ts` (modify) + `workspaceStore.test.ts` (modify)
- `frontend/src/features/workspace/FilterPanel.tsx` (modify) + `FilterPanel.test.tsx` (modify/create)
- `frontend/src/features/workspace/ActiveFilterChips.tsx` (create) + `ActiveFilterChips.test.tsx` (create)
- `frontend/src/features/workspace/DateRangePresets.tsx` (create) + `DateRangePresets.test.tsx` (create)
- `frontend/src/features/workspace/views/TableView.tsx` (modify) + `TableView.test.tsx` (modify/create)
- `frontend/src/features/workspace/views/MapView.tsx` (modify)
- `frontend/src/hooks/useFilteredReports.ts` (modify — add `limit`/`offset` params for pagination)
- `frontend/src/lib/types.ts` (modify — add `DatePreset` type)
- `src/fala_gavea/presentation/api/main.py` (modify — SPA catch-all guard)
- `tests/test_spa_fallback.py` (create — backend regression)

## Decisions captured

- **D-009** (already recorded in design intent): staged draft+Apply supersedes D-008 live cross-filtering.

---

## Steps

### Step 1: Extend workspaceStore — committed/draft split + panel state

Refactor `frontend/src/store/workspaceStore.ts` with the following additions:

**New state fields:**
- `draftFilters: WorkspaceFilters` — initialized equal to `filters` (`{}`). This is what the panel edits.
- `panelOpen: boolean` — default `true`. Controls collapse.
- `loadedPresetName: string | null` — default `null`. Set by Phase B when a saved preset is loaded.
- `draftFilterName: string` — default `''`. The name the user types for a new preset (used by Phase B save gesture).

**New / modified actions:**
- `setDraftFilter(patch: Partial<WorkspaceFilters>)` — merges into `draftFilters` only. Does NOT touch committed `filters`.
- `applyFilters()` — `filters = { ...draftFilters }`. Views re-fetch only when this runs.
- `clearFilters()` — resets BOTH: `filters = {}`, `draftFilters = {}`, `loadedPresetName = null`, `draftFilterName = ''`.
- `discardDraft()` — resets `draftFilters = { ...filters }` (reverts draft to committed, i.e. cancel editing). Also resets `loadedPresetName` if it was set (a discard of a loaded-but-unapplied preset).
- `removeFilter(key: keyof WorkspaceFilters)` — removes `key` from BOTH `filters` and `draftFilters` immediately (chip remove). Recompute objects without that key using destructuring.
- `setBbox(bbox: string | undefined)` — direct manipulation: set `bbox` on BOTH `filters.bbox` and `draftFilters.bbox` immediately. Does not leave a pending diff (direct manipulation bypasses staging).
- `setSemanticQuery(q: string)` — now writes to **draft only** (`setDraftFilter({ semanticQuery: q })`).
- `togglePanel()` — flips `panelOpen`.
- `setLoadedPresetName(name: string | null)` — called by Phase B; sets `loadedPresetName`.
- `setDraftFilterName(name: string)` — called by Phase B save gesture; sets `draftFilterName`.
- `isDirty(): boolean` — implement using `get()` internally, identical in pattern to `structuredFilters`: `isDirty: () => { const { draftFilters, filters } = get(); const keys = ['urgency','status','type_id','since','until','bbox','semanticQuery'] as const; return keys.some(k => draftFilters[k] !== filters[k]); }`. Consumers must always use `useWorkspaceStore(s => s.isDirty())` — never destructure `isDirty` from the raw store object (avoids stale-closure/re-render pitfalls with Zustand method stores).
- Keep `setFilter` as a thin alias to `setDraftFilter` for internal back-compat only (remove external callsites if none exist outside FilterPanel).
- Keep `structuredFilters()` reading committed `filters` (unchanged).

**Migration note:** `setBbox` is already called from `MapView` — it must continue to commit immediately (both slices). The existing `FilterPanel` calls `setFilter` — this becomes `setDraftFilter` in Step 2.

- **Files:** `frontend/src/store/workspaceStore.ts` (modify), `frontend/src/store/workspaceStore.test.ts` (modify)
- **References:** `product-design/conventions.md § Frontend`
- **Interface:** `filters`, `draftFilters`, `panelOpen`, `loadedPresetName`, `draftFilterName`, `setDraftFilter(patch)`, `applyFilters()`, `clearFilters()`, `discardDraft()`, `removeFilter(key)`, `setBbox(bbox)`, `setSemanticQuery(q)`, `togglePanel()`, `setLoadedPresetName(name)`, `setDraftFilterName(name)`, `isDirty()`, `structuredFilters()`.
- **Verify:** `cd frontend && npx tsc --noEmit` clean; `npm run test` passes.
- **Tests:** Update `workspaceStore.test.ts`:
  - `setDraftFilter` changes draft, not committed.
  - `applyFilters` copies draft to committed; `isDirty()` is `false` after apply.
  - `isDirty()` is `true` after `setDraftFilter`, `false` after `clearFilters`.
  - `setBbox` updates BOTH slices; `isDirty()` is `false` after `setBbox`.
  - `removeFilter('urgency')` drops key from BOTH slices.
  - `discardDraft` resets `draftFilters` to match `filters`.
  - `clearFilters` resets all name fields to defaults.

### Step 2: Four-section FilterPanel — layout, Apply/Limpar, dirty indicator, draft-loss guard, collapse

Rewrite `frontend/src/features/workspace/FilterPanel.tsx` as the four-section left panel. All panel filter inputs now read `draftFilters` and write via `setDraftFilter`. The panel width becomes `w-72` (288 px).

**Layout (outer wrapper: `w-72 flex flex-col h-full bg-white border-r border-gray-200`):**

**Section 1 — Preset bar (fixed header, `border-b py-2 px-3`):**
```
[ filter name or "Sem nome" ] [ Salvar ] [ Carregar ▾ ]
```
- The filter name shown is: `loadedPresetName` if set and not dirty; `loadedPresetName + " *"` if set and dirty; `"Sem nome"` if null.
- "Salvar" and "Carregar" buttons: placeholder `opacity-50 cursor-not-allowed` and `disabled` until Phase B wires them. Add a `title="Disponível em breve"` tooltip so users see it is coming. Do NOT hide them — they anchor the layout for Phase B.
- Result count: `{count} relato{count !== 1 ? 's' : ''}` as a small badge (right side of the bar).

**Section 2 — Active chips (`border-b py-2 px-3 max-h-20 overflow-y-auto`):**
- Renders `<ActiveFilterChips />` (Step 3). If no committed filters, show `<p className="text-xs text-gray-400">Nenhum filtro ativo.</p>`.

**Section 3 — Draft controls (`flex-1 overflow-y-auto py-2 px-3 flex flex-col gap-3`):**
- All `<Select>` inputs (Tipo, Urgência, Status) now read `draftFilters` and call `setDraftFilter`.
- Date section: `<DateRangePresets />` (Step 4).
- Semantic search `<Input>` reads `draftFilters.semanticQuery`, calls `setSemanticQuery` (which routes to draft in Step 1).
- **Dirty indicator:** `{isDirty() && <p aria-live="polite" className="text-xs text-amber-600">Filtros alterados — clique Aplicar</p>}`
- **Aplicar** primary button (calls `applyFilters()`), disabled when `!isDirty()`.
- **Limpar** ghost button (calls `clearFilters()`).
- Enter key in any text input triggers `applyFilters()`.

**Section 4 — NL assistant footer (fixed, `border-t py-2 px-3`):**
- Placeholder layout only (Phase C wires the logic):
  ```
  <p className="text-xs text-gray-500 font-medium mb-1">Assistente de filtros</p>
  <div className="flex gap-1">
    <Input placeholder="Descreva o filtro..." className="h-7 text-xs flex-1" disabled />
    <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" disabled title="Disponível em breve">→</Button>
  </div>
  <p className="text-xs text-gray-400 mt-1">Em breve: filtros por linguagem natural</p>
  ```

**Collapse toggle:** a `<button>` pinned to the right edge of the panel (absolutely positioned), calls `togglePanel()`. When `panelOpen === false`, the panel renders only the toggle button (with a chip-count badge showing `isDirty() ? '!' : count || ''`). Add dynamic `aria-label`: when open, `"Recolher painel de filtros"`; when closed, `` `Expandir painel de filtros — ${count} resultado${count !== 1 ? 's' : ''}` ``.

**Draft-loss guard:** in the outer workspace component (`WorkspacePage.tsx` or wherever routing happens), intercept navigation events — if `isDirty()`, show a Radix `<AlertDialog>` with "Você tem filtros não aplicados. Deseja descartá-los?" and two actions: "Descartar e sair" (calls `discardDraft()`, then navigates) and "Voltar". This guard must be placed in the component that owns the SPA router navigation, not in the FilterPanel itself.

- **Files:** `frontend/src/features/workspace/FilterPanel.tsx` (modify), `frontend/src/features/workspace/FilterPanel.test.tsx` (modify/create)
- **References:** `product-design/standards.md § Frontend`
- **Depends on:** Step 1
- **Verify:** editing a Select shows dirty indicator and does NOT change the result count until Aplicar is clicked; Aplicar updates views; Limpar resets everything; the collapse toggle hides/shows the panel; Enter in the semantic input triggers apply.
- **Tests:** mock store with `draftFilters`, `isDirty`, `applyFilters`, `clearFilters`, `discardDraft`, `togglePanel`:
  - Aplicar button disabled when `isDirty()` is false; enabled when true.
  - Dirty indicator text renders when `isDirty()` is true.
  - Clicking Aplicar calls `applyFilters`.
  - Limpar calls `clearFilters`.
  - Enter in semantic input calls `applyFilters`.
  - Section 4 NL placeholder is visible and disabled.
  - Collapse toggle calls `togglePanel`; when `panelOpen=false` panel collapses.

### Step 3: ActiveFilterChips component

Create `frontend/src/features/workspace/ActiveFilterChips.tsx`:

Renders one chip per committed `filters` key that has a value. Chip label format:
- `type_id`: resolve via `useReportTypes` → "Tipo: {name}" (fallback to id if not found).
- `urgency`: "Urgência: {Alta|Média|Baixa}".
- `status`: "Status: {Pendente|Em análise|Encaminhado|Resolvido}".
- `since`: "De: {formatted date pt-BR}".
- `until`: "Até: {formatted date pt-BR}".
- `bbox`: "Área do mapa".
- `semanticQuery`: `Busca: "{q}" ` (truncated to 20 chars if long).

Each chip is a `<span>` with an `×` button that calls `removeFilter(key)`. Wrap chips in an `aria-live="polite"` region. Empty state renders nothing (caller renders the "Nenhum filtro ativo" paragraph).

- **Files:** `frontend/src/features/workspace/ActiveFilterChips.tsx` (create), `frontend/src/features/workspace/ActiveFilterChips.test.tsx` (create)
- **Depends on:** Step 1
- **Verify:** chips reflect committed `filters`, not `draftFilters`; × calls `removeFilter`; all 7 filter keys produce correct labels.
- **Tests:** with mock store `filters={urgency:'alta',type_id:'x'}`, renders "Urgência: Alta" and resolves type_id label; clicking × calls `removeFilter('urgency')`.

### Step 4: DateRangePresets component

Create `frontend/src/features/workspace/DateRangePresets.tsx`:

Renders a preset selector row + optional custom date inputs. Presets:
```
Hoje | Últ. 7 dias | Últ. 15 dias | Últ. 30 dias | Este mês | Personalizado
```

On preset selection (except "Personalizado"):
- Compute `since` and `until` as ISO date strings (`YYYY-MM-DD`) for the corresponding relative range (using `new Date()`, not a library).
- Call `setDraftFilter({ since, until })`.
- Show the resolved absolute dates as small text below: "De: 07/06/2026 Até: 21/06/2026".

On "Personalizado":
- Show two native `<input type="date">` for since/until, reading and writing `draftFilters.since` / `draftFilters.until` via `setDraftFilter`.

Active preset is highlighted (ring or background). When `draftFilters.since` and `draftFilters.until` do not match any preset's computed range, show "Personalizado" as active (fallback).

Export `type DatePreset = 'hoje' | 'ultimos7' | 'ultimos15' | 'ultimos30' | 'estemes' | 'personalizado'` in `frontend/src/lib/types.ts`.

- **Files:** `frontend/src/features/workspace/DateRangePresets.tsx` (create), `frontend/src/features/workspace/DateRangePresets.test.tsx` (create), `frontend/src/lib/types.ts` (modify — add `DatePreset`)
- **Depends on:** Step 1
- **Verify:** selecting "Últ. 15 dias" populates draft `since`/`until` with correct dates and shows resolved absolute dates; selecting "Personalizado" reveals native date inputs; resolved dates update when the current day changes.
- **Tests:** selecting "Últ. 7 dias" calls `setDraftFilter` with `since` = 7 days ago and `until` = today; selecting "Personalizado" shows date inputs; "Personalizado" is auto-selected when `draftFilters.since` doesn't match a preset.

### Step 5: SPA routing fix — catch-all guard + api.ts alignment

Two independent fixes that together resolve the confirmed production defect (research-000129 F2):

**Backend — `src/fala_gavea/presentation/api/main.py`:**
In `spa_fallback`, add a guard before returning `index.html`. Define a set of known API path prefixes:
```python
_API_PREFIXES = {
    "auth", "reports", "report_types", "forwardings",
    "nl", "admin", "health", "docs",
}
```
In `spa_fallback`, before the `FileResponse(STATIC_DIR / "index.html")` line, add:
```python
first_segment = full_path.split("/")[0] if full_path else ""
if first_segment in _API_PREFIXES:
    return JSONResponse({"detail": "Not Found"}, status_code=404)
```
This ensures that `GET /report_types` (slashless) falls through to Starlette's normal routing (which 307-redirects to `/report_types/`), rather than being swallowed by the SPA catch-all.

**Frontend — `frontend/src/lib/api.ts`:**
Align the `getReportTypes()` and `getForwardings()` calls to use trailing-slash canonical URLs:
- `getReportTypes()`: change `"/report_types"` to `"/report_types/"`.
- `getForwardings()`: change `` `/forwardings${q}` `` — the `buildQuery` function appends `?...` if params exist, so add a trailing slash to the base: `` `/forwardings/${q}` `` becomes `` `/forwardings/${q}` `` with the base path as `"/forwardings/"` then appending `q` (which starts with `?` or is `""`). Concrete fix: `return request<Forwarding[]>("GET", \`/forwardings/${q ? q : ''}\`)` → `return request<Forwarding[]>("GET", \`/forwardings/\${q}\`)` where base is `"/forwardings/"`. Simplest: `buildQuery` already returns `"?..."` or `""`, so `\`/forwardings/\${q}\`` works.

**Backend test — `tests/test_spa_fallback.py` (create):**
- `GET /report_types` (no trailing slash) returns `Content-Type: application/json` and NOT `text/html` (i.e., the catch-all did not intercept it).
- `GET /forwardings` (no trailing slash, authenticated) returns `application/json`.
- `GET /some/unknown/path` returns `text/html` (SPA index served for unknown paths).

- **Files:** `src/fala_gavea/presentation/api/main.py` (modify), `frontend/src/lib/api.ts` (modify), `tests/test_spa_fallback.py` (create)
- **Verify:** `uv run pytest tests/test_spa_fallback.py -v` passes; the Tipos combobox populates in a production-built SPA; `uv run pyright src/` clean.
- **Tests:** the three assertions above in `test_spa_fallback.py`.

### Step 6: TableView — sort, full-text dialog, pagination, score column, density toggle

Rework `frontend/src/features/workspace/views/TableView.tsx`. No external table library required — use local sort state.

**Column sort:**
Add `sortConfig: { key: SortKey; dir: 'asc' | 'desc' } | null` to local state (`useState`). `SortKey = 'text' | 'urgency' | 'status' | 'created_at' | 'score'`. On `<th>` click: toggle direction if same key, else set key + `'asc'`. Sort icon: `↑` (asc), `↓` (desc), `⇅` (inactive sortable). Apply `Array.from(features).sort(...)` before rendering. For `score`: items with `null` score sort last. Preferred pattern (WAI-ARIA Authoring Practices): wrap the sort control in a `<button>` inside each sortable `<th>` — `<th aria-sort="ascending"><button onClick={...} onKeyDown={...} aria-label="Ordenar por Data">Data ↑</button></th>`. The `aria-sort` attribute belongs on the `<th>`, not the inner `<button>`. This avoids the need for `tabIndex={0}` on `<th>` directly.

**Full-text reader (Radix Dialog):**
Truncate text in cell to 80 chars + "…" as before. Add a "Ler relato" visually-small link inside the text cell (only visible on hover or always at text-xs). On click: open a `<Dialog>` with:
- Full `p.text` (no truncation).
- Tipo, Urgência, Status, Data fields below the text.
- A "Similares" button inside the dialog (calls `setSimilarSeed(p.id)` then closes dialog).
- Focus trapped inside; `Escape` closes; focus returns to the triggering element (`useRef` on the trigger).

Install `@radix-ui/react-dialog` if not already in `package.json`. Use the existing shadcn-style component at `frontend/src/components/ui/dialog.tsx` if it exists; otherwise create a minimal wrapper.

**Pagination:**
- Update `useFilteredReports` to accept an optional `options?: { limit?: number; offset?: number }` parameter. When provided, override the `limit` (default 200) and add `offset` to the query body.
- In `TableView`, add `page: number` local state (default 0) and `PAGE_SIZE = 50`.
- Pass `{ limit: PAGE_SIZE, offset: page * PAGE_SIZE }` to `useFilteredReports`.
- Render below the table: `< Anterior | Página {page + 1} de {Math.ceil(total / PAGE_SIZE)} | Próxima >` with correct disabled states.
- Show above the table header: `{total} relatos encontrados — página {page + 1} de {Math.ceil(total / PAGE_SIZE)}` in `text-xs text-gray-500`.
- On page change: reset to page 0 whenever the store's committed `filters` change (use `useEffect` on `filters` to reset `page`). Also reset to page 0 when `sortConfig` changes — add `sortConfig` to the same `useEffect` dependency array (or a second `useEffect`). Rationale: changing sort column while on page 2 would otherwise show page 2 of the new ordering, which is confusing.

**Score column:**
- Visible only when `data?.ranked_by === 'similarity'`. Add a `score` property to `ReportFeature.properties` if not already present (or read from `features` array directly — the hook maps from `ReportQueryItem` which has `score`). Pass `score` through the hook's `features` mapping or as a parallel array.
- Column header: "Relevância" with a `title="Pontuação de similaridade semântica (0–1)"` tooltip.
- Cell: `score != null ? score.toFixed(2) : '—'`, followed by `<span className="sr-only">{score >= 0.7 ? ' (alta)' : score >= 0.4 ? ' (média)' : ' (baixa)'}</span>` for WCAG 1.4.1 compliance (color not the sole differentiator). Color: `score >= 0.7` → `text-green-600`; `0.4–0.7` → `text-amber-600`; `< 0.4` → `text-gray-400`.

**Density toggle:**
- Add `dense: boolean` local state (default `false`).
- A small `<button>` in a toolbar above the table: "Compacto / Confortável" (or an icon). Toggles `dense`.
- `<TableRow className={dense ? 'h-7' : 'h-10'}>` (or equivalent Tailwind).

- **Files:** `frontend/src/features/workspace/views/TableView.tsx` (modify), `frontend/src/features/workspace/views/TableView.test.tsx` (modify/create), `frontend/src/hooks/useFilteredReports.ts` (modify), `frontend/src/lib/types.ts` (modify — add `score?: number | null` to `ReportFeature.properties` or map it separately)
- **Depends on:** Step 1 (for store shape; TableView also re-reads committed `filters` via `useFilteredReports`)
- **Verify:** clicking a column header sorts rows; clicking the text cell opens a Dialog with full text; Escape closes the Dialog; pagination next/prev changes the page and re-fetches; score column appears only when a semantic query is active (`ranked_by === 'similarity'`); density toggle changes row height.
- **Tests:** render with mock `useFilteredReports` returning 60 items + `total=60`; clicking "Data" header sorts by `created_at`; clicking "Data" again while on page 2 resets to page 0; "Ler relato" button opens dialog with full text; page 2 is accessible via "Próxima"; score column renders only when `ranked_by='similarity'`; score cell with value 0.8 has `sr-only` text "(alta)".

### Step 7: MapView — "Filtrar nesta área" button

Replace the primary draw gesture with a single-button filter and optionally retain draw as a secondary option.

**Primary change — "Filtrar nesta área" button:**
Add a `mapRef` via `useRef<L.Map | null>(null)` and assign it via the `ref` prop on `<MapContainer>` (or use `useMap()` inside a child component). Add a button to the overlay:
```
[ Filtrar nesta área ]  [ Limpar área ]  (existing draw button retained as secondary, optional)
```
On "Filtrar nesta área" click: read `map.getBounds()`, compute `minLat, minLon, maxLat, maxLon`, call `setBbox(\`\${minLat},\${minLon},\${maxLat},\${maxLon}\`)`. This commits bbox to both slices immediately (per Step 1's `setBbox` semantics).

**Optional: retain draw with live Rectangle:**
If the draw button is kept, render a `<Rectangle bounds={[corner1, cursor]} .../>` while drawing = true and corner1 is set (provides visual feedback that was missing). This requires `useMapEvents` to also track `mousemove` while drawing. **This is optional** — implement only if straightforward; omit otherwise to keep scope clean.

**"Limpar área"** button: calls `setBbox(undefined)`. Disable when `currentBbox` is undefined.

- **Files:** `frontend/src/features/workspace/views/MapView.tsx` (modify)
- **Depends on:** Step 1 (for `setBbox` semantics)
- **Verify:** clicking "Filtrar nesta área" sets bbox to the current map bounds; because `setBbox` commits to both slices immediately, the count updates WITHOUT pressing Aplicar, and a "Área do mapa" chip must appear immediately in Section 2 (ActiveFilterChips); "Limpar área" clears bbox and removes the chip immediately.
- **Tests:** MapView is map-heavy and difficult to unit-test; add a note in the test file documenting the manual test: (1) zoom to a region, click "Filtrar nesta área", observe count changes; (2) click "Limpar área", observe full result set returns.

### Step 8: Wire WorkspacePage draft-loss guard + regression pass

**Draft-loss guard in WorkspacePage:**
In the component that contains the SPA routing (`WorkspacePage.tsx` or the root `App.tsx`), add an `AlertDialog` triggered when the user navigates away while `isDirty()` is true. Implementation depends on the router: if using `react-router-dom` v6+, use the `useBlocker` hook (v6.8+) or a `beforeunload` event listener as fallback.

```tsx
const isDirty = useWorkspaceStore((s) => s.isDirty())
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty) { e.preventDefault(); e.returnValue = '' }
  }
  window.addEventListener('beforeunload', handleBeforeUnload)
  return () => window.removeEventListener('beforeunload', handleBeforeUnload)
}, [isDirty])
```

For SPA-internal navigation (link clicks within the app), show a Radix `<AlertDialog>` with "Você tem filtros não aplicados. Deseja descartá-los?" — "Descartar e sair" (calls `discardDraft()`, then navigates) and "Voltar" (cancels).

**Pending action: close plan-000131:**
Run `python .claude/skills/scripts/pending.py done --source plan-000131 --type implement` to close the superseded pending entry.

**Final regression checks:**
- `cd frontend && npm run test` — all tests pass.
- `cd frontend && npx tsc --noEmit` — no type errors.
- `uv run pytest tests/` — backend tests pass including `test_spa_fallback.py`.
- `uv run ruff check src/ tests/` — no lint errors.
- `uv run pyright src/` — no type errors.

- **Files:** `frontend/src/app/WorkspacePage.tsx` or `frontend/src/App.tsx` (modify — add draft-loss guard)
- **Depends on:** Steps 1–7
- **Verify:** navigate to `/report` while filters are dirty — AlertDialog appears; choosing "Descartar e sair" navigates; choosing "Voltar" stays; refreshing browser with dirty filters shows native browser confirmation.
- **Docs:** N/A (internal guard, no user-visible docs change needed)
- **Tests:** unit-test: `useWorkspaceStore.isDirty()` returns true when `draftFilters !== filters`; the `beforeunload` listener is registered when `isDirty` is true and removed when false.

---

## Test plan

1. **Filter staging:** edit a Select in the panel → verify result count does NOT change; press Aplicar → count changes. Press Limpar → all filters reset, count shows total.
2. **Dirty indicator:** set a draft filter → "Filtros alterados" text appears; press Aplicar → text disappears.
3. **Active chips:** press Aplicar with urgency=alta → chip "Urgência: Alta" appears in Section 2; click × → urgency removed from both slices immediately.
4. **Date presets:** click "Últ. 15 dias" → resolved dates show below preset bar; draft `since`/`until` populated; press Aplicar → count changes to last-15-days window.
5. **Tipos combobox (production regression):** build SPA (`npm run build`), start FastAPI (`uv run uvicorn ...`), navigate to workspace → Tipos dropdown shows all report types. (Was empty before Step 5.)
6. **Table sort:** click "Data" header → rows sort newest-first; click again → oldest-first; click "Urgência" → high urgency at top.
7. **Full-text dialog:** click "Ler relato" on a truncated row → Dialog opens with full text; press Esc → Dialog closes, focus returns to trigger.
8. **Pagination:** with more than 50 results → "Próxima" button enabled; click → page 2 loads; "Anterior" enabled; count caption shows "Página 2 de N".
9. **Score column:** type a semantic query, press Aplicar → score column appears with values 0.00–1.00, color-coded.
10. **Map "Filtrar nesta área":** pan/zoom map to a region, click "Filtrar nesta área" → markers update to show only visible area; click "Limpar área" → all markers return.
11. **Collapse toggle:** click collapse button → panel hides; map/table expands; badge shows count; click again → panel restores.
12. **Draft-loss guard:** set draft filters, click a nav link → AlertDialog appears; choose "Descartar e sair" → navigates; choose "Voltar" → stays on workspace.

---

## Implementation Summary

**Completed:** 8/8 steps | **Iterations used:** 8 (1 per step) | **Partial/Failed:** 0

### Steps

- [x] Step 1: Extend workspaceStore — committed/draft split + panel state (`3072bc1`)
- [x] Step 2: Four-section FilterPanel — layout, Apply/Limpar, dirty indicator, collapse (`e171ca4`)
- [x] Step 3: ActiveFilterChips component (`6f45974`)
- [x] Step 4: DateRangePresets component + `DatePreset` type (`bda600f`)
- [x] Step 5: SPA routing fix — catch-all guard + api.ts trailing slash (`76df8e2`)
- [x] Step 6: TableView — sort, full-text dialog, pagination, score column, density toggle (`0ad89ab`)
- [x] Step 7: MapView — "Filtrar nesta área" button (`7a81e10`)
- [x] Step 8: WorkspacePage draft-loss guard + regression pass (`b1076c3`)

### Quality Gate

- Frontend: 80/80 tests pass, TypeScript clean
- Backend: 141/142 tests pass (1 pre-existing failure in `test_static_spa.py`), ruff clean, pyright 66 pre-existing errors (unchanged)
- Code review (check-000138): 1 HIGH fixed (getForwardings URL), 3 MEDIUM/LOW fixed, 4 advisory deferred
- Files changed: 21 files, +1985/-333 lines

### Key Decisions / Learnings

- `filtersKey = JSON.stringify(filters)` pattern used in `useEffect` to reset page on filter change (avoids object identity pitfalls)
- `setBbox` commits to both slices immediately (bypasses staging by design — MapView direct manipulation)
- `@radix-ui/react-dialog` already installed; reused for both TableView full-text and WorkspacePage blocker dialog
- plan-000131 pending entry closed (superseded by this plan)
