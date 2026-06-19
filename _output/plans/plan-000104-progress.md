# Progress -- Plan 000104

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns

- `api.ts` uses `request<T>(method, path, options)` + `buildQuery(params)` helper — reuse for new endpoints.
- `useReports` in `hooks/useReports.ts` passes `ReportFilters` to `api.getReportsGeoJSON` via `useQuery` with `staleTime: 30_000`.
- Auth via `useAuth()` from `@/auth/AuthContext` — exposes `user.role`.
- shadcn-style UI components live in `src/components/ui/` — use `button`, `input`, `select`, `label`, `table`, `dialog`, `badge`.
- `@tanstack/react-query` v5 API: `useQuery({queryKey, queryFn, ...})`, `useMutation({mutationFn, ...})`.
- `keepPreviousData` in react-query v5 = `placeholderData: keepPreviousData` imported from `@tanstack/react-query`.
- No `zustand` or `react-leaflet-cluster` in package.json yet — Step 1 must install them first.
- `ReportFeature.properties.id` is the unique report id string.
- `CreateForwardingDialog` is prop-driven (`selectedIds: string[]`, `open`, `onSuccess`, `onClose`) — keep it that way; don't couple to store.
- `SelectionBar` currently takes `count`, `onCreateForwarding`, `onClear` as props — will be lifted to read from store in Step 7.
- Rollback branch: `pre-plan-000104`

## Iteration Log

<!-- Steps append findings here as they complete -->

### Step 1 — 2026-06-19 — SUCCESS

- `@types/react-leaflet-cluster` does not exist on npm — skipped as planned.
- `react-leaflet-cluster@4.x` requires React 19 (peer dep `@react-leaflet/core@3.0.0` → `react@^19`). Installed `react-leaflet-cluster@2.1.0` instead — that version declares `react@^18.0.0` as peer dep and `react-leaflet@^4.0.0`, compatible with project's React 18 + react-leaflet ^4.2.1.
- `zustand` installed without issues (no peer dep conflicts).
- New types appended to `frontend/src/lib/types.ts`: `TopicItem`, `TopicListResponse`, `ReportSearchResult`, `ChatRequest`, `ChatResponse`, `WorkspaceFilters`.
- `npm run build` — clean, 230 modules, no TypeScript errors.
- `npm run lint` — 5 pre-existing issues (2 errors in `api.test.ts` _url unused vars; 3 warnings in shadcn UI files for react-refresh). None caused by Step 1 changes.
- Commit: `4094ba6` — `plan-000104 step 1: add zustand + react-leaflet-cluster deps and new workspace types`

### Step 2 — 2026-06-19 — SUCCESS

- Added 4 new methods to `frontend/src/lib/api.ts`: `getTopics`, `getSimilarReports`, `searchReports`, `chat`.
- Imported `TopicListResponse`, `ReportSearchResult`, `ChatRequest`, `ChatResponse` from `./types`.
- `getTopics` spreads `ReportFilters` with `min_docs` default 3; authenticated (no `public: true`).
- `getSimilarReports` defaults `n=5`; authenticated.
- `searchReports` defaults `n=50`; `public: true` (no auth).
- `chat` POSTs to `/nl/chat`; authenticated.
- `npm run build` — clean, 230 modules, no TypeScript errors.
- `npm run lint` — same 5 pre-existing issues; no new errors from Step 2 changes.
- Commit: `3270909` — `plan-000104 step 2: api layer getTopics, getSimilarReports, searchReports, chat`

### Step 3 — 2026-06-19 — SUCCESS

- Created `frontend/src/store/workspaceStore.ts` with full `WorkspaceState` interface and `useWorkspaceStore` via `zustand` `create`.
- `structuredFilters()` implemented as a store method (not stored state): destructures `semanticQuery` out of `filters` and returns the remainder as `ReportFilters`.
- `toggleSelect` uses `Set` mutation on a new `Set` copy for immutability.
- `clearFilters` resets `filters` to `{}` but leaves `selectedIds` unchanged — confirmed by test.
- `defaultViewsForRole` exported as a standalone function (not stored state).
- Created `frontend/src/store/workspaceStore.test.ts` with 4 vitest tests covering all specified behaviors.
- Test reset pattern: `useWorkspaceStore.setState({...})` called in `afterEach` (no `getInitialState()` needed).
- All 20 tests pass (4 new store tests + 16 pre-existing).
- `npm run build` — clean, 230 modules, no TypeScript errors.
- Commit: `038378d` — `plan-000104 step 3: zustand workspaceStore + tests`

### Step 4 — 2026-06-19 — SUCCESS

- Created `frontend/src/features/workspace/WorkspacePage.tsx`: flex-row shell with `<FilterPanel />` left rail + `<ViewToggleBar />` + view placeholder grid. `useEffect` on `user?.role` resets `activeViews` to role defaults via `useWorkspaceStore.setState`.
- Created `frontend/src/features/workspace/FilterPanel.tsx`: full filter implementation reading/writing from `useWorkspaceStore` (type, urgency, status, since, until). Semantic query input enabled and live (writes to `store.setSemanticQuery`). Uses `useReportTypes()` for type dropdown.
- Created `frontend/src/features/workspace/ViewToggleBar.tsx`: chip per ViewId with `aria-pressed`, `aria-label`, focus-return-to-bar on deactivate via `barRef.current?.focus()` in `requestAnimationFrame`. `topics` and `chat` chips hidden for non-agent/non-admin users. `similars` visible to all.
- Modified `frontend/src/App.tsx`: commented out `MapPage` lazy import; added `WorkspacePage` lazy import; `/` route now renders `<WorkspacePage />`.
- `npm run build` — clean, 185 modules (MapPage chunk gone from entry), no TypeScript errors.
- Commit: `13c0890` — `plan-000104 step 4: WorkspacePage shell + ViewToggleBar + FilterPanel + App routing`

### Step 5 — 2026-06-19 — SUCCESS

- Created `frontend/src/hooks/useSemanticSearch.ts`: wraps `api.searchReports(q, 50)` in `useQuery` with `enabled: q.trim().length > 0`, `staleTime: 30_000`, `placeholderData: keepPreviousData`.
- Created `frontend/src/hooks/useFilteredReports.ts`: single source of truth hook. Reads `filters` from store via `useWorkspaceStore(s => s.filters)`, destructures `semanticQuery` from `structuredFilters`. Calls `useQuery` directly (not `useReports`) to support `placeholderData: keepPreviousData` on the geo query. Exports `intersectByScore` as a named pure function.
- `intersectByScore` builds a `Map` from geojson features by `properties.id`, then iterates `semanticResults` in score order to produce the intersection, preserving semantic ranking.
- Created `frontend/src/hooks/useFilteredReports.test.ts`: 4 pure unit tests for `intersectByScore` — intersection by id, score-order preservation, empty-intersection case, and `semanticTruncated` logic check.
- All 24 tests pass (4 new + 20 pre-existing). `npm run build` — clean, 185 modules, no TypeScript errors.
- Commit: `ffc15a9` — `plan-000104 step 5: useFilteredReports + useSemanticSearch + intersection tests`

### Step 6 — 2026-06-19 — SUCCESS

- Created `frontend/src/features/workspace/views/MapView.tsx`: migrates MapContainer from MapPage, reads `features` from `useFilteredReports()`, `selectedIds`/`toggleSelect`/`setBbox` from `useWorkspaceStore`, `typeMap` from `useReportTypes()`, `isAgent` from `useAuth()`.
- `BboxDrawHandler` inner component uses `useMapEvents` for click-to-draw rectangle: first click sets corner1, second click computes min/max lat-lon bbox string and calls `setBbox`. Uses local `useState` for corner1.
- `MarkerClusterGroup` (default import from `react-leaflet-cluster@2.1.0`) wraps `<ReportMarkers>` — no changes to ReportMarkers needed (already returns `<>`).
- Overlay bbox buttons: "Desenhar área" (min-h-44px, aria-pressed, disabled during draw) and "Limpar área" (shown only when `currentBbox` set) — positioned `absolute top-2 right-2 z-[1000]`.
- `WorkspacePage.tsx`: lazy-loads MapView via `lazy(() => import(...).then(m => ({ default: m.MapView })))`. View grid changed from `flex-wrap content-start` to `flex flex-1 overflow-auto gap-2 p-2`. When `viewId === 'map'`, renders `<Suspense>` with pulse fallback inside a `div.flex-1.min-h-[300px].min-w-[300px]`. All other viewIds remain placeholders.
- `npm run build` — clean, 251 modules (up from 185; MapView gets its own 203.67 kB lazy chunk). No TypeScript errors, no new lint issues.
- Commit: `a9ba6c8` — `plan-000104 step 6: MapView widget with clustering and bbox draw`

### Step 7 — 2026-06-19 — SUCCESS

- Created `frontend/src/features/workspace/views/TableView.tsx`: table with 6 columns (checkbox, text truncated to 80 chars, tipo, urgência, status, data). Reads from `useFilteredReports()`, `useWorkspaceStore`, `useReportTypes()`. Row click and checkbox both call `toggleSelect(id)`. Urgency uses Unicode shape prefix (▲/●/▼) for a11y. Status uses PT-BR labels.
- Created `frontend/src/features/workspace/views/TableView.test.tsx`: 5 vitest tests covering render, type name display, urgency label, row click calls `toggleSelect`, checkbox click calls `toggleSelect`. All mocks use selector-function pattern matching the store's `create` API.
- `ReportProperties` uses `author_id` (not `user_id`) and has no `latitude`/`longitude` fields — mock corrected accordingly.
- Updated `frontend/src/features/workspace/WorkspacePage.tsx`: lazy-imports `TableView`; renders it in the view grid when `viewId === 'table'` inside a `div.flex-1.min-h-[300px]` with Suspense pulse fallback. Adds `SelectionBar` and `CreateForwardingDialog` conditionally for `isAgent` (agent or admin), reading `selectedIds`/`clearSelection` from store and managing `showCreateDialog` with `useState`.
- All 29 tests pass (5 new + 24 pre-existing). Build clean: 257 modules, `TableView-*.js` lazy chunk 2.59 kB.
- Commit: `fbb0a05` — `plan-000104 step 7: TableView + shared selection via store + SelectionBar in WorkspacePage`

### Steps 8-10 — 2026-06-19 — SUCCESS

- Created `frontend/src/hooks/useTopics.ts`: wraps `api.getTopics` in `useQuery` with `retry: false`; strips `semanticQuery` from store filters before passing as `ReportFilters`. Used `eslint-disable-next-line` for the intentionally-unused destructured `_semanticQuery`.
- Created `frontend/src/hooks/useSimilarReports.ts`: wraps `api.getSimilarReports` in `useQuery` with `enabled: !!similarSeedId`.
- Created `frontend/src/hooks/useChat.ts`: wraps `api.chat` in `useMutation`.
- Created `frontend/src/features/workspace/views/TopicsView.tsx`: agent/admin guard (after hooks), loading/503/error/empty/success states, lists topics with terms and count.
- Created `frontend/src/features/workspace/views/SimilarsView.tsx`: persistent caption always visible, no-seed/loading/503/error/empty/success states, urgency labels with Unicode shapes.
- Created `frontend/src/features/workspace/views/ChatView.tsx`: all hooks before early return (rules-of-hooks compliance), conversation list with `aria-live="polite"`, cited report id buttons call `setSimilarSeed`, 503 handling.
- Updated `frontend/src/features/workspace/WorkspacePage.tsx`: lazy-imports all 3 new views; renders them in the view grid for `topics`, `similars`, `chat` viewIds inside `div.flex-1.min-h-[300px].min-w-[280px]` with Suspense pulse fallback.
- Key fix: initial drafts had hooks after early role-guard returns — moved all hooks before the guard to satisfy `react-hooks/rules-of-hooks`.
- `npm run build` — clean, 263 modules (up from 257), 3 new lazy chunks: TopicsView, SimilarsView, ChatView. No TypeScript errors.
- `npm run lint` — 6 issues all pre-existing (3 errors: `_url` in api.test.ts x2, `_sq` in workspaceStore.ts; 3 warnings in shadcn/AuthContext files). No new errors from steps 8-10.
- Commit: `205124f` — `plan-000104 steps 8-10: TopicsView + SimilarsView + ChatView IA widgets`

### Step 11 — 2026-06-19 — SUCCESS

- Imported `useFilteredReports` into `FilterPanel.tsx`; destructured `count` and `semanticTruncated`.
- Added `aria-live="polite" aria-atomic="true" sr-only` region for screen-reader announcements (semantic truncation vs. count).
- Added visible count `<span>` in the header row between the "Filtros" title and "Limpar" button.
- Added `semanticTruncated` amber notice below semantic query `<Input>`.
- Semantic query `<Input>` was already enabled (writes to `setSemanticQuery`) — no change needed.
- Urgency options already had text labels ("Alta", "Média", "Baixa") — no change needed.
- `npm run build` — clean, 263 modules, no TypeScript errors.
- `npm run lint` — same 6 pre-existing issues; no new errors.
- Commit: `7aa2441` — `plan-000104 step 11: a11y live count and semantic truncation notice in FilterPanel`

### Step 12 — 2026-06-19 — SUCCESS

- Deleted `frontend/src/features/map/MapPage.tsx`, `FiltersSidebar.tsx`, `FiltersSidebar.test.tsx`.
- Cleaned `frontend/src/App.tsx`: removed commented-out MapPage import line (file is now clean).
- `CreateForwardingDialog.test.tsx` had no MapPage dependency — passes unchanged (2 tests).
- Created `frontend/src/features/workspace/FilterPanel.test.tsx` with 2 tests (renders + live count). Mock pattern: `useWorkspaceStore: () => mockStore` (no-arg call, not selector pattern). `shows live count` uses `getAllByText` because count appears in both the sr-only aria-live div and the visible `<span>`.
- All 28 tests pass (9 test files). Build clean: 263 modules, 21 chunks. Lint: 6 pre-existing issues only (3 errors in api.test.ts/_sq; 3 warnings in shadcn/AuthContext files).
- Commit: `10a9f64` — `plan-000104 step 12: remove MapPage/FiltersSidebar, update tests, final verification`
