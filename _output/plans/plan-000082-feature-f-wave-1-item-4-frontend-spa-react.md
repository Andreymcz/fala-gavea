# Plan 000082 | FEATURE-F fala-gavea | 2026-06-18 14:04 UTC | wave-1-item-4-frontend-spa-react | Review: standard
plan_format_version: 1

source: roadmap-00001 -- Wave 1, Item 4: Frontend (mapa de relatos + painel de encaminhamentos). User brief supersedes D-006 (static HTML + Leaflet + Alpine.js) with a modern SPA stack.

## Brief (verbatim)

roadmap 71 item 4. Quero que voce explore tecnologias de front end mais modernas para a iteracao ficar mais fluida. ou seja, podemos fugir das paginas estaticas e ficar com um visual mais moderno

## Agent Interpretation

Implement Wave 1, Item 4 of roadmap-00001 (the frontend), but **replacing the static-pages
approach** locked in by Decision D-006 (`HTML estatico + Leaflet + Alpine.js`) with a modern
Single-Page Application for a more fluid interaction and a more modern look.

Stack decided with the user (3 AskUserQuestion answers, 2026-06-18):

1. **Framework**: React 18 + Vite + TypeScript (SPA), with `react-leaflet` for the map,
   `@tanstack/react-query` for server-state (cache/refetch/optimistic UI), and `react-router-dom`
   for client-side routing.
2. **Styling/UI**: Tailwind CSS + shadcn-style headless components (Radix primitives), reusing
   the existing `design-standards.md` palette as Tailwind theme tokens.
3. **Scope**: full SPA covering all 4 surfaces -- public map, citizen report form, agent
   forwardings dashboard, login/register. Covers journeys JM-TB-001 (cidadao) and JM-TB-002 (agente).

This plan delivers the SPA and the minimal backend enablers it requires:
- A new `GET /auth/me` endpoint so the SPA knows the current user's **role** (the JWT only carries
  `sub`; role is resolved server-side -- see `dependencies.py:60`).
- A guarded **StaticFiles mount + SPA catch-all fallback** in `main.py` so the built SPA is served
  same-origin by FastAPI in production (per the original D-006 serving model, which this keeps).

**CORS is intentionally NOT added**: dev uses a Vite proxy (same-origin), prod serves the built
SPA from FastAPI StaticFiles (same-origin). Avoiding a cross-origin surface aligns with security
invariant S1/C1 (local-first) and keeps the auth path simple (constitution T2).

## Decision impact (supersedes D-006)

This plan contradicts and supersedes **D-006** (`Frontend HTML estatico + Leaflet sem framework JS`).
Step 11 records a new decision **D-007** via `apply_marker.py --marker DECISION_APPEND` and updates
the dependent docs: `standards.md § Frontend`, `design-standards.md` (build/stack notes), `CLAUDE.md`,
`conventions.md` (ARCHITECTURE_DESCRIPTION frontend clause), and `product-design-as-coded.md §8`.
The conceptual intent (map-centric civic app, urgency colors, geolocation, multi-select for
forwarding, NL chat placeholder) is **unchanged** -- only the implementation technology changes.

## Scope

In scope: React+Vite+TS SPA (4 screens), Tailwind+shadcn-style UI, `GET /auth/me`, StaticFiles
SPA serving, frontend tooling (ESLint/Prettier/Vitest), `.gitignore` updates, and the design-doc
updates that supersede D-006.

Out of scope (future items):
- Semantic search / similar reports / NL chat (Items 5-7, Wave 2). Step 7 leaves a **disabled,
  clearly-stubbed** search box + chat affordance placeholder wired to no backend, so the layout is
  ready but no fake behavior ships.
- Image upload (photo_url remains a free-text URL field, per D-003).
- Admin ReportType CRUD UI (admin manages types via API/seed for now). The report-type dropdown
  consumes `GET /report_types` read-only.
- Marker clustering (`leaflet.markercluster`) -- noted as a follow-up; not required for PoC volumes.

## Files

### New files -- frontend project (`frontend/`)
- `frontend/package.json`, `frontend/package-lock.json` (generated)
- `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`
- `frontend/index.html`
- `frontend/tailwind.config.ts`, `frontend/postcss.config.js`
- `frontend/.eslintrc.cjs`, `frontend/.prettierrc`, `frontend/.env.example`
- `frontend/vitest.config.ts`, `frontend/src/test/setup.ts`
- `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`
- `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `frontend/src/lib/queryClient.ts`, `frontend/src/lib/utils.ts`
- `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/useAuth.ts`, `frontend/src/auth/RequireAuth.tsx`
- `frontend/src/components/ui/*` (Button, Input, Textarea, Select, Dialog, Toast/Toaster, Card, Table, Badge, Label)
- `frontend/src/components/layout/Header.tsx`, `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/features/map/MapPage.tsx`, `ReportMarkers.tsx`, `FiltersSidebar.tsx`, `ReportPopup.tsx`, `SelectionBar.tsx`, `CreateForwardingDialog.tsx`, `markerIcons.ts`
- `frontend/src/features/report/ReportFormPage.tsx`
- `frontend/src/features/forwardings/ForwardingsPage.tsx`, `ForwardingRow.tsx`, `StatusSelect.tsx`
- `frontend/src/features/auth/LoginPage.tsx`, `RegisterPage.tsx`
- `frontend/src/hooks/useReports.ts`, `useReportTypes.ts`, `useForwardings.ts`
- Tests: `frontend/src/lib/api.test.ts`, `frontend/src/auth/AuthContext.test.tsx`, `frontend/src/features/map/FiltersSidebar.test.tsx`, `frontend/src/features/forwardings/StatusSelect.test.tsx`

### New files -- backend
- `tests/test_static_spa.py` (SPA fallback + /auth/me coverage may also live in test_auth.py)

### Modified files
- `src/fala_gavea/presentation/api/routers/auth.py` (add `GET /me`)
- `src/fala_gavea/presentation/schemas/auth.py` (reuse `UserResponse` for /me; add `MeResponse` only if shape differs)
- `src/fala_gavea/presentation/api/main.py` (StaticFiles mount + SPA catch-all fallback, guarded by dir existence)
- `tests/test_auth.py` (add /auth/me tests)
- `.gitignore` (add `frontend/node_modules/`, `frontend/dist/`, `static/`)
- `README.md` or `CLAUDE.md` (frontend build/run instructions)
- `product-design/project/standards.md` (§ Frontend rewrite; § Testing frontend addition)
- `product-design/project/design-standards.md` (stack/build note)
- `product-design/conventions.md` (ARCHITECTURE_DESCRIPTION frontend clause)
- `product-design/project/product-design-as-coded.md` (§8 + changelog)
- `CLAUDE.md` (Stack: Frontend line)

> Note: `product-design-as-intended.md` D-006 is a Human(markers) file -- it is updated only via
> `apply_marker.py` (Step 11), never by hand.

---

## Steps

### Step 1: Backend enablers -- `GET /auth/me` + SPA static serving

Add the two backend pieces the SPA needs. No CORS (dev uses Vite proxy; prod is same-origin).

**`presentation/api/routers/auth.py`** (modify -- append):
```python
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id, email=current_user.email, name=current_user.name,
        role=current_user.role.value, created_at=current_user.created_at,
    )
```
(Import `User` from `domain.entities.user` and `get_current_user` from `dependencies`.)

**`presentation/api/main.py`** (modify): after all routers are included, mount static serving
**only if the build output exists**, so tests and the dev API (no `static/`) are unaffected. API
routers are registered first and therefore win over the catch-all.
```python
from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).resolve().parents[3] / "static"  # <repo>/static

def _mount_spa(app: FastAPI) -> None:
    if not STATIC_DIR.exists():
        return
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
```
Call `_mount_spa(app)` at the end of `create_app()`. Verify `parents[3]` resolves to the repo root
(`main.py` is at `src/fala_gavea/presentation/api/main.py` -> parents: api[0], presentation[1],
fala_gavea[2], src[3]); if the repo root is the parent of `src`, use `parents[4]` and place `static/`
there. **Confirm the exact depth during implementation** by printing `STATIC_DIR` once.

- **Files**: `src/fala_gavea/presentation/api/routers/auth.py` (modify), `src/fala_gavea/presentation/api/main.py` (modify), `tests/test_auth.py` (modify), `tests/test_static_spa.py` (create)
- **References**: `product-design/project/standards.md § Backend §5, §8`, `product-design/project/constitution.md T2`, `product-design/project/product-design-as-intended.md §4`
- **Interface**: Adds `GET /auth/me` -> `UserResponse` (200 auth, 401 unauth); `_mount_spa(app)` helper guarded by `STATIC_DIR.exists()`
- **Verify**: `uv run pytest tests/test_auth.py tests/test_static_spa.py -v` green; `uv run ruff check src/ tests/` clean
- **Tests**: `GET /auth/me` returns the registered user's email+role with a valid token; returns 401 without/with bad token. SPA fallback test creates a temp `static/index.html`, reloads app, asserts unknown path returns the index HTML while `/auth/me` still 401s (API precedence). If patching `STATIC_DIR` at runtime is awkward, assert the helper no-ops when dir absent and unit-test the resolution logic.
- **Traces**: JM-TB-002, US-002
- [ ] Done

---

### Step 2: Scaffold the Vite + React + TS project with Tailwind

Create the `frontend/` project. Build output goes to the repo `static/` dir (served by Step 1).
Dev uses a Vite proxy so the app calls same-origin relative URLs.

`frontend/package.json` deps: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`,
`leaflet`, `react-leaflet`, `clsx`, `tailwind-merge`, `class-variance-authority`, Radix primitives
(`@radix-ui/react-dialog`, `@radix-ui/react-select`, `@radix-ui/react-label`, `@radix-ui/react-toast`).
devDeps: `vite`, `@vitejs/plugin-react`, `typescript`, `tailwindcss`, `postcss`, `autoprefixer`,
`eslint` + React/TS plugins, `prettier`, `vitest`, `@testing-library/react`,
`@testing-library/jest-dom`, `jsdom`, `@types/leaflet`, `@types/react`, `@types/react-dom`.

`frontend/vite.config.ts`:
```ts
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../static", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: Object.fromEntries(
      ["/auth", "/reports", "/report_types", "/forwardings"].map((p) => [
        p, { target: "http://localhost:8000", changeOrigin: true },
      ]),
    ),
  },
  resolve: { alias: { "@": "/src" } },
});
```
`frontend/.env.example`: `VITE_API_URL=` (empty = same-origin / proxy; can point at a full URL if
not using the proxy). `frontend/index.html` mounts `#root` and loads `/src/main.tsx`.
Tailwind config scans `./index.html` and `./src/**/*.{ts,tsx}`. Add `.gitignore` entries
(`frontend/node_modules/`, `frontend/dist/`, `static/`).

- **Files**: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/index.html`, `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/.eslintrc.cjs`, `frontend/.prettierrc`, `frontend/.env.example`, `.gitignore` (modify)
- **References**: `product-design/project/standards.md § Frontend`, `general/coding-standards.md § Stack-conditional (TypeScript)`
- **Interface**: `npm run dev` (proxied dev server), `npm run build` (-> `../static`), `npm run lint`, `npm run test`
- **Verify**: `cd frontend && npm install && npm run build` produces `static/index.html` + `static/assets/`; `npm run lint` clean
- **Tests**: N/A (tooling/config only)
- **Docs**: covered in Step 11 (README build/run section)
- [ ] Done

---

### Step 3: Tailwind theme tokens + shadcn-style UI primitives

Encode the `design-standards.md` palette as Tailwind theme tokens and build the headless component
kit the screens reuse. `frontend/src/index.css` defines CSS variables and `@tailwind` layers.
`tailwind.config.ts` maps semantic colors: `urgency.alta` `#E53E3E`, `urgency.media` `#DD6B20`,
`urgency.baixa` `#3182CE`, `search` `#805AD5`, `success` `#38A169`, `error` `#E53E3E`,
`neutral` `#718096`, `background` `#F7FAFC`.

`frontend/src/lib/utils.ts` exports `cn()` (clsx + tailwind-merge). Build `components/ui/`:
`Button` (cva variants), `Input`, `Textarea`, `Label`, `Select` (Radix), `Dialog` (Radix),
`Toast` + `Toaster` + `useToast` (Radix), `Card`, `Table` (thin wrappers), `Badge`
(urgency/status variants). Components are accessible (Radix gives focus/ARIA) per design-standards §7
and WCAG AA contrast.

- **Files**: `frontend/src/index.css`, `frontend/tailwind.config.ts` (refine), `frontend/src/lib/utils.ts`, `frontend/src/components/ui/*` (button, input, textarea, label, select, dialog, toast, toaster, card, table, badge)
- **References**: `product-design/project/design-standards.md § Visual Design (Color Palette, Typography), § UX Patterns (Accessibility, Feedback)`
- **Depends on**: Step 2
- **Interface**: Exports UI primitives from `@/components/ui/*` and `cn` from `@/lib/utils`; `useToast()` hook + `<Toaster/>` mount point
- **Verify**: `npm run build` succeeds; a temporary render of `<Button>`/`<Badge>` shows palette colors
- **Tests**: covered by component tests in later steps (Badge variants asserted in Step 9 StatusSelect test context)
- [ ] Done

---

### Step 4: API client, shared types, and TanStack Query setup

Create the typed API layer used by every screen.

`frontend/src/lib/types.ts`: TS interfaces mirroring backend schemas -- `User` (`{id,email,name,role,created_at}`,
`role: "citizen"|"agent"|"admin"`), `ReportType` (`{id,name,description,active,created_at}`),
`ReportFeature` (GeoJSON `properties: {id,text,urgency,status,report_type_id,created_at}`,
`geometry.coordinates: [lon,lat]`), `ReportDetail`, `Forwarding`/`ForwardingResponse`
(`{id,institution,proposed_solution,status,agent_id,reports: ReportSummary[],created_at,updated_at}`),
`Urgency`, `ReportStatus`, `ForwardingStatus` string unions.

`frontend/src/lib/api.ts`: a `fetch` wrapper that reads `import.meta.env.VITE_API_URL` (default `""`),
attaches `Authorization: Bearer <token>` from `localStorage["fala_gavea_token"]`, parses
`{detail}` errors into a thrown `ApiError(status, detail)`, and on **401 dispatches a
`window` event `auth:unauthorized`** (AuthContext listens -> logout+redirect). Typed methods:
- `login(email, password)`: POST `/auth/token` as **`application/x-www-form-urlencoded`** with
  `username`+`password` (matches `OAuth2PasswordRequestForm`); returns `{access_token}`.
- `register(...)`: POST `/auth/register` (JSON).
- `me()`: GET `/auth/me`.
- `getReportsGeoJSON(filters)`, `getReport(id)`, `createReport(body)`.
- `getReportTypes()`.
- `getForwardings(filters)`, `getForwarding(id)`, `createForwarding(body)`,
  `updateForwardingStatus(id, status)`, `updateForwarding(id, body)`.

`frontend/src/lib/queryClient.ts`: a configured `QueryClient` (sane `staleTime`, retry off for 4xx).

- **Files**: `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/queryClient.ts`, `frontend/src/lib/api.test.ts`
- **References**: `product-design/project/standards.md § Backend §8 (API conventions), § Frontend §3 (Auth state)`, `product-design/project/product-design-as-intended.md §10`
- **Depends on**: Step 2
- **Interface**: Exports `api` object (typed methods above), `ApiError`, the `QueryClient` instance, and all shared TS types
- **Verify**: `npm run test -- api` passes; `npm run build` typechecks clean
- **Tests**: when `api.login` is called, it sends a urlencoded body with `username`/`password` and stores nothing itself (storage is AuthContext's job); when a request gets 401, `ApiError` is thrown and the `auth:unauthorized` event fires (assert via mocked `fetch` + event listener)
- [ ] Done

---

### Step 5: Auth context, route guard, app shell, and router

Wire global auth state and the SPA skeleton.

`frontend/src/auth/AuthContext.tsx`: holds `{token, user, login, logout, isLoading}`. On mount, if a
token exists, calls `api.me()` to hydrate `user` (and logs out on failure). `login(email,password)`
calls `api.login`, stores token in `localStorage["fala_gavea_token"]`, then `api.me()`. Listens for
the `auth:unauthorized` event to force logout. `useAuth()` hook exposes it.
`frontend/src/auth/RequireAuth.tsx`: redirects to `/login` if unauthenticated; optional
`roles?: Role[]` prop redirects to `/` (with a toast) if the user's role is not allowed.

`frontend/src/components/layout/Header.tsx`: nav with links shown by role -- Mapa (all),
Novo relato (citizen+), Encaminhamentos (agent/admin), Entrar/Sair. `AppLayout.tsx` renders Header +
`<Outlet/>` + `<Toaster/>`. `App.tsx` sets up `react-router-dom` routes:
`/` MapPage (public), `/login`, `/register`, `/report` (RequireAuth), `/agent`
(RequireAuth roles=[agent,admin]). `main.tsx` wraps `<QueryClientProvider>` + `<AuthProvider>` +
`<BrowserRouter>`.

- **Files**: `frontend/src/auth/AuthContext.tsx`, `frontend/src/auth/useAuth.ts`, `frontend/src/auth/RequireAuth.tsx`, `frontend/src/components/layout/Header.tsx`, `frontend/src/components/layout/AppLayout.tsx`, `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/auth/AuthContext.test.tsx`
- **References**: `product-design/project/standards.md § Frontend §3 (Auth state), §2 (Navigation)`, `product-design/project/product-design-as-intended.md §4 (Permission model)`
- **Depends on**: Step 4, Step 3
- **Interface**: Exports `AuthProvider`, `useAuth()`, `RequireAuth`; route table with public `/` and guarded `/report`, `/agent`
- **Verify**: `npm run build` succeeds; app boots to MapPage at `/`; visiting `/agent` while logged out redirects to `/login`
- **Tests**: when a stored token is present, AuthContext hydrates `user` from a mocked `api.me()`; when `me()` rejects, it logs out and clears localStorage; the `auth:unauthorized` event triggers logout (BrowserRouter wrapped in test)
- **Traces**: REQ-MC-001, JM-TB-001, JM-TB-002
- [ ] Done

---

### Step 6: Login + Register screens

`frontend/src/features/auth/LoginPage.tsx`: email + password form, submits via `useAuth().login`,
shows error toast "Email ou senha incorretos." on 401 (per design-standards §6), redirects to `/` on
success (or to the `from` location if redirected by RequireAuth). Link to `/register`.
`RegisterPage.tsx`: name + email + password, calls `api.register` (creates a citizen), then auto-logs
in and redirects to `/`. On 409 shows "Este email ja esta cadastrado."

- **Files**: `frontend/src/features/auth/LoginPage.tsx`, `frontend/src/features/auth/RegisterPage.tsx`
- **References**: `product-design/project/design-standards.md § Form Patterns, § Feedback Patterns`, `product-design/project/product-design-as-intended.md §1 (registration open as citizen)`
- **Depends on**: Step 5
- **Interface**: Routed at `/login` and `/register`
- **Verify**: manual -- login with seeded agent credentials lands on the map with agent nav visible; bad password shows the error toast
- **Tests**: N/A (thin form wrappers; auth logic covered in Step 5). Add a smoke render test only if time permits.
- **Traces**: US-001
- [ ] Done

---

### Step 7: Map screen -- Leaflet map, markers, popups, filters

`frontend/src/features/map/MapPage.tsx`: full-height `react-leaflet` `MapContainer` centered on
Gavea (`[-22.9731, -43.2272]`, zoom 15) with an OpenStreetMap tile layer, plus a `FiltersSidebar`.
`hooks/useReports.ts` (`useReportTypes.ts`) fetch `/reports/geojson` (with active filters) and
`/report_types` via TanStack Query; build an `id -> name` map for type labels.

- `ReportMarkers.tsx`: render a marker per feature; `markerIcons.ts` provides urgency-colored
  divIcons (alta=red, media=orange, baixa=blue, search=purple reserved for Wave 2). Each marker has
  a `title` for screen readers (design-standards §7).
- `ReportPopup.tsx`: popup with tipo (resolved name), texto, urgencia Badge, status Badge, data.
- `FiltersSidebar.tsx`: controls for tipo (`type_id`), urgencia, status, data_de (`since`),
  data_ate (`until`); updates query params -> refetch. Empty state: "Nenhum relato registrado na
  Gavea ainda. Seja o primeiro!" (design-standards §5).
- **Wave-2 placeholders**: a **disabled** semantic-search input and a minimized chat affordance with
  tooltip "Disponivel em breve" -- present for layout, wired to nothing (no fake results).

Agent multi-select and the create-forwarding flow are added in Step 8 (this step renders read-only
markers for everyone).

- **Files**: `frontend/src/features/map/MapPage.tsx`, `ReportMarkers.tsx`, `ReportPopup.tsx`, `FiltersSidebar.tsx`, `markerIcons.ts`, `frontend/src/hooks/useReports.ts`, `frontend/src/hooks/useReportTypes.ts`, `frontend/src/features/map/FiltersSidebar.test.tsx`
- **References**: `product-design/project/design-standards.md § Map Interaction Patterns, § Empty States`, `product-design/project/standards.md § Frontend §4 (Map conventions)`, `product-design/project/product-design-as-intended.md §8`
- **Depends on**: Step 4, Step 3
- **Interface**: `/` route renders the public map; exports `useReports(filters)` and `useReportTypes()`
- **Verify**: `npm run build` ok; with the dev API seeded, markers render colored by urgency and the type filter narrows results
- **Tests**: when a status filter is selected in `FiltersSidebar`, the `onChange`/query-params callback fires with the chosen value (RTL); urgency->color mapping unit-tested in `markerIcons`
- **Traces**: US-003, JM-TB-001, JM-TB-002
- [ ] Done

---

### Step 8: Agent multi-select + Create Forwarding dialog (on the map)

For authenticated agent/admin users only (`useAuth().user?.role`), add report selection on the map
and the forwarding-creation flow (JM-TB-002 steps 4-7).

- `SelectionBar.tsx`: a floating bar/button visible when `selectedIds.size >= 1`, labeled
  "Criar encaminhamento (N)" with the live count (design-standards §4).
- Marker selection: agents get a checkbox/toggle in the popup (or click-to-select) that adds/removes
  the report id from selection state held in `MapPage`.
- `CreateForwardingDialog.tsx`: Radix Dialog with `institution` (Input) and `proposed_solution`
  (Textarea), client-side validation matching backend (institution 3-200, solution 20-5000), submit
  -> `api.createForwarding({institution, proposed_solution, report_ids})`. On success: success toast
  "Encaminhamento criado para {institution}.", clear selection, invalidate the reports query (the
  linked reports flip to `encaminhado`), and offer a link to `/agent`.

Non-agents never see selection UI (markers stay read-only). Enforcement remains server-side
(`require_any_role`) -- the UI gating is convenience only.

- **Files**: `frontend/src/features/map/SelectionBar.tsx`, `frontend/src/features/map/CreateForwardingDialog.tsx`, `frontend/src/features/map/MapPage.tsx` (modify -- selection state), `ReportPopup.tsx` (modify -- agent checkbox), `frontend/src/hooks/useForwardings.ts`
- **References**: `product-design/project/design-standards.md § Map Interaction Patterns (selection, modal), § Feedback Patterns`, `product-design/project/product-design-as-intended.md §8 (Selecao multipla), §13 US-002, §15 JM-TB-002`
- **Depends on**: Step 7, Step 5
- **Interface**: Exports `useForwardings` mutation hooks; selection state contained in MapPage
- **Verify**: manual -- as an agent, select >=1 marker, the floating button shows the count, the dialog creates a forwarding, a success toast shows, and the selected reports' status becomes `encaminhado` on refetch
- **Tests**: `CreateForwardingDialog` blocks submit and shows a field error when `proposed_solution` < 20 chars (RTL); the create mutation calls `api.createForwarding` with the selected ids (mocked)
- **Traces**: US-002, JM-TB-002
- [ ] Done

---

### Step 9: Agent dashboard -- forwardings table

`frontend/src/features/forwardings/ForwardingsPage.tsx` at `/agent` (RequireAuth roles=[agent,admin]):
a `Table` of forwardings from `useForwardings()` (`GET /forwardings`) with columns institution,
n_relatos (`reports.length`), status Badge, data, acoes. Filters for status and institution
(design-standards §3 of Map-Centric app / JM-TB-002). `ForwardingRow.tsx` expands on click to list the
linked reports (text + urgency + status). `StatusSelect.tsx` is an inline Radix Select that calls
`api.updateForwardingStatus(id, status)` and optimistically updates (TanStack Query mutation +
invalidate), showing a toast on success/failure. Empty state: "Nenhum encaminhamento criado ainda."

- **Files**: `frontend/src/features/forwardings/ForwardingsPage.tsx`, `ForwardingRow.tsx`, `StatusSelect.tsx`, `frontend/src/hooks/useForwardings.ts` (extend), `frontend/src/features/forwardings/StatusSelect.test.tsx`
- **References**: `product-design/project/design-standards.md § Component Inventory (Tabela de encaminhamentos), § Empty States`, `product-design/project/product-design-as-intended.md §15 JM-TB-002 post-conditions`
- **Depends on**: Step 5, Step 4, Step 3
- **Interface**: `/agent` route; `useForwardings()` list + `useUpdateForwardingStatus()` mutation
- **Verify**: manual -- agent sees created forwardings; changing status in the inline select persists (reload confirms) and shows a toast
- **Tests**: when a new status is chosen in `StatusSelect`, `api.updateForwardingStatus` is called with the row id and chosen value (RTL + mocked api); status->Badge variant mapping asserted
- **Traces**: US-002, JM-TB-002
- [ ] Done

---

### Step 10: Citizen report form with geolocation

`frontend/src/features/report/ReportFormPage.tsx` at `/report` (RequireAuth, any authenticated user):
report-type Select (from `useReportTypes()`), urgencia Select (alta/media/baixa with color hints),
texto Textarea (10-2000 chars, live counter), lat/lon Inputs with a "Usar minha localizacao" button
calling `navigator.geolocation.getCurrentPosition` (fallback: editable fields + inline alert
"Geolocalizacao nao disponivel. Preencha latitude e longitude manualmente." per design-standards §6),
optional photo_url Input (helper: "Cole a URL de uma foto"). Submit -> `api.createReport`,
success toast "Relato registrado com sucesso!", redirect to `/` (the new report appears on the map
after refetch). Client validation mirrors backend §10 (text length, lat [-90,90], lon [-180,180]).

- **Files**: `frontend/src/features/report/ReportFormPage.tsx`, `frontend/src/hooks/useReports.ts` (extend -- create mutation)
- **References**: `product-design/project/design-standards.md § Form Patterns, § Feedback Patterns`, `product-design/project/product-design-as-intended.md §8 (Formulario geolocalizado), §13 US-001, §15 JM-TB-001`, `product-design/project/standards.md § Security §1 (validation)`
- **Depends on**: Step 5, Step 4, Step 3
- **Interface**: `/report` route; `useCreateReport()` mutation
- **Verify**: manual -- citizen submits a report, sees the success toast, lands on the map with the new marker; "Usar minha localizacao" fills lat/lon
- **Tests**: submit is blocked with a validation message when `text` < 10 chars (RTL); geolocation success path sets lat/lon (mock `navigator.geolocation`)
- **Traces**: US-001, JM-TB-001
- [ ] Done

---

### Step 11: Build wiring, docs, and supersede D-006

Make the SPA runnable end-to-end and bring the design docs in line with the new stack.

1. **Build/run docs**: add a Frontend section to `README.md` (or `CLAUDE.md` Build & Run) covering
   `cd frontend && npm install`, `npm run dev` (proxied to `uv run uvicorn ...`), `npm run build`
   (-> `static/`), then `uv run uvicorn fala_gavea.presentation.api.main:app` serves the built SPA
   same-origin. Update `CLAUDE.md` Stack line: Frontend = React + Vite + TypeScript + Tailwind +
   shadcn-style (react-leaflet), served by FastAPI StaticFiles.
2. **standards.md § Frontend**: replace the static-HTML/Alpine.js subsections with the SPA structure
   (`frontend/src/` layout, Vite build to `static/`, Tailwind tokens, Radix components, TanStack
   Query, react-router). Add a **§ Testing > Frontend** subsection (Vitest + React Testing Library;
   mock `fetch`/api; `npm run test`).
3. **design-standards.md**: add a short build/stack note (SPA, Tailwind tokens from the palette);
   keep the UX/visual intent (palette, map conventions, empty states) intact.
4. **conventions.md**: update the `ARCHITECTURE_DESCRIPTION` frontend clause to "React + Vite SPA
   (TypeScript, Tailwind, react-leaflet) servido pelo FastAPI StaticFiles".
5. **Supersede D-006**: run
   `python .claude/skills/scripts/apply_marker.py --marker DECISION_APPEND` to append **D-007**
   ("Frontend SPA React+Vite+TS+Tailwind supersedes D-006") with context (brief: more fluid/modern
   UI), decision (the chosen stack + same-origin serving, no CORS), and consequences (build step
   introduced; richer interaction; npm toolchain added; D-006 superseded). Reference D-006 in the
   body. Confirm the exact CLI flags from the script's `--help`.
6. **as-coded §8 + changelog**: update `product-design-as-coded.md §8 (User Experience Patterns)`
   from "Not yet implemented" to the implemented SPA surfaces, and append a v5 changelog entry
   (this is an Agent-maintained file; post-skill may also do this -- coordinate to avoid duplication).

- **Files**: `README.md` and/or `CLAUDE.md` (modify), `product-design/project/standards.md` (modify), `product-design/project/design-standards.md` (modify), `product-design/conventions.md` (modify), `product-design/project/product-design-as-coded.md` (modify via post-skill or here), `product-design/project/product-design-as-intended.md` (D-007 via apply_marker.py only)
- **References**: `general/report-conventions.md`, `product-design/conventions.md (As-Intended/As-Coded Registry)`, `product-design/project/product-design-as-intended.md (Decisions section, D-006)`
- **Depends on**: Step 2 (stack names final)
- **Interface**: N/A
- **Verify**: `git grep -n "Alpine"` shows only historical/changelog references; `apply_marker.py` reports D-007 appended; docs build/read consistently
- **Tests**: N/A (docs/config)
- **Docs**: this step IS the docs update
- [ ] Done

---

## Review Log

Inline review (Review depth: **standard** -- new toolchain + auth/token handling + supersedes a
design decision; auto=standard, floor=light, no flag -> effective=standard).

| Perspective | Decision | Notes |
|-------------|----------|-------|
| SEC | Adopted | No CORS surface (Vite proxy in dev, same-origin StaticFiles in prod) -- aligns with S1/C1 local-first. JWT in `localStorage` is a known XSS exposure; accepted for PoC (consistent with prior D-003/standards §Frontend), mitigated by React's default output escaping and no `dangerouslySetInnerHTML`. Role-based UI is convenience only; server-side `require_role`/`require_any_role` remain the enforcement boundary (T2). `GET /auth/me` reuses `get_current_user` -- no new auth path. |
| ARCH | Adopted | Clean-architecture backend untouched except an additive endpoint + a guarded static mount; no domain/application changes. Frontend isolated in `frontend/`, built to `static/`. Supersession of D-006 recorded as D-007 with dependent-doc updates (Step 11). |
| API | Adopted | SPA consumes the existing 14 endpoints unchanged. Critical contract captured: `/auth/token` is form-urlencoded (OAuth2PasswordRequestForm); geojson carries `report_type_id` (joined client-side with `/report_types`); status/urgency enums mirrored as TS unions. |
| FE/UX | Adopted | Map-centric layout, urgency color tokens, geolocation, multi-select->forwarding, empty states, toasts -- all preserved from design-standards. Wave-2 search/chat shipped as disabled placeholders (no fake behavior). |
| A11y | Adopted | Radix primitives give focus management + ARIA; markers carry `title`; labels on all inputs; palette meets WCAG AA per design-standards §7. |
| TEST | Adopted | Backend: pytest for `/auth/me` + SPA fallback. Frontend: Vitest + RTL for api client (urlencoded login, 401 event), AuthContext hydration/logout, FiltersSidebar, StatusSelect, CreateForwardingDialog validation, ReportForm validation/geolocation. Standards §Testing updated to define frontend testing. |
| PERF | Deferred | No marker clustering (`leaflet.markercluster`) -- acceptable at PoC report volumes; noted as follow-up if marker counts grow. TanStack Query caching reduces refetch churn. |
| DATA | Adopted | Forwarding creation flips report status to `encaminhado` server-side; the SPA invalidates the reports query so the map reflects the transition. A report may appear in multiple forwardings (D-D) -- UI does not prevent re-selecting an already-forwarded report. |

Deferred / follow-ups:
- **Marker clustering** (PERF) -- add when volumes warrant.
- **Refresh tokens / token expiry UX** -- out of scope (D-003 PoC auth); on 401 the SPA logs out and redirects to login.
- **Image upload** -- photo_url stays free-text (D-003).
- **Admin ReportType CRUD UI** -- types managed via API/seed for now.
- **`STATIC_DIR` depth** -- confirm `parents[N]` resolves to the dir holding `static/` during Step 1 implementation.
