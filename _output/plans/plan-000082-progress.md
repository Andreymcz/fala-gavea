# Progress -- Plan 000082

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns

- Project root: `c:\Users\arodrigues\Pesquisa\doutourado\2026.1\INF2921\inf2921-grupo-c\fala-gavea`
- Backend source: `src/fala_gavea/`
- Main entry: `src/fala_gavea/presentation/api/main.py`
- Auth router: `src/fala_gavea/presentation/api/routers/auth.py`
- Dependencies: `src/fala_gavea/presentation/api/dependencies.py`
- Schemas: `src/fala_gavea/presentation/schemas/auth.py`
- Tests: `tests/`
- Frontend target: `frontend/` (to be created)
- SPA build output: `static/` (repo root)
- Package manager: uv (Python), npm (frontend)
- Test command: `uv run pytest`
- Lint: `uv run ruff check src/ tests/`

## Iteration Log

## Step 1 (Backend enablers)
- STATUS: SUCCESS
- STATIC_DIR path confirmed: `parents[4]` resolves to repo root (`c:\Users\arodrigues\Pesquisa\doutourado\2026.1\INF2921\inf2921-grupo-c\fala-gavea`). The plan file noted `parents[3]` but that is `src/` not the repo root — `parents[4]` is correct.
- UserResponse schema had role field: yes (already present as `role: str` in `presentation/schemas/auth.py`)
- Pre-existing bug fixed: `jwt_service.py` was calling `InvalidCredentialsError("Token expired")` / `InvalidCredentialsError("Invalid token")` but `InvalidCredentialsError.__init__()` takes no arguments. Fixed to `InvalidCredentialsError()`. This bug was latent and exposed by the new `test_me_invalid_token` test.
- 11 tests pass (6 pre-existing + 3 new /auth/me tests + 2 new SPA tests); ruff clean.

## Step 2 (Vite Scaffold)
- STATUS: SUCCESS
- npm install: success (408 packages, warnings about deprecated deps — not blocking)
- npm run build: success, static/ created: yes (static/index.html + static/assets/)
- First npm install attempt failed with EBUSY on esbuild.exe (Windows file lock from partial install); second attempt succeeded without intervention
- Tailwind warning "No utility classes detected" is expected for placeholder src files — not an error
- node_modules/ and static/ correctly gitignored via .gitignore additions

## Step 3 (UI Primitives)
- STATUS: SUCCESS
- Components created: button.tsx, input.tsx, textarea.tsx, label.tsx, select.tsx, dialog.tsx, toast.tsx, toaster.tsx, card.tsx, table.tsx, badge.tsx
- Also created: src/lib/utils.ts (cn helper), updated src/index.css (Tailwind @layer base)
- Build succeeded: yes (30 modules transformed, 142.62 kB JS + 15.79 kB CSS)
- Toast approach: custom store (not Radix) for simpler test integration

## Step 4 (API client)
- STATUS: SUCCESS
- Tests passed: yes (4/4)
- Build typecheck: clean (30 modules, 142.62 kB JS)
- Key API patterns: login uses URLSearchParams (OAuth2PasswordRequestForm), 401 dispatches auth:unauthorized event
- Fix applied: added `frontend/src/vite-env.d.ts` with `/// <reference types="vite/client" />` — was missing, causing `ImportMeta.env` TS error
- vite.config.ts updated with `test: { environment: "jsdom" }` so localStorage/window are available in vitest

## Step 5 (Auth + Router)
- STATUS: SUCCESS
- AuthContext.test.tsx: 3 tests passed (hydrate from token, logout on me() reject, logout on auth:unauthorized event)
- api.test.ts: 4 tests still passing (total 7/7)
- Build: clean (100 modules transformed, 222.60 kB JS + 16.52 kB CSS)
- Placeholder stubs created for: MapPage, ReportFormPage, ForwardingsPage, LoginPage, RegisterPage
- Lazy code-splitting works: each page gets its own chunk in the build output
- React Router future flag warnings in tests are cosmetic (v6→v7 migration notices), not errors

## Step 7 (Map screen)
- STATUS: SUCCESS
- Tests: 10 passed (3 new FiltersSidebar tests + 7 pre-existing)
- Build: clean (221 modules transformed, MapPage chunk 252.89 kB + 15.04 kB CSS)
- Fix applied: `vite.config.ts` `setupFiles` was `[]` — wired to `["./src/test/setup.ts"]` so `@testing-library/jest-dom` matchers (`toBeInTheDocument`) work
- Fix applied: test imported `type MapFilters` as unused value — changed to import only `FiltersSidebar`
- Added `@testing-library/user-event@^14.6.1` to devDependencies (was missing)
- MapPage state (`selectedIds`, `mapFilters`) designed to be extended by Step 8 agent selection UI

## Step 10 (Report form)
- STATUS: SUCCESS
- Tests: 12 passed (2 new ReportFormPage tests + 10 pre-existing)
- Build: clean (223 modules transformed)
- Fix applied: test imported `beforeEach` from vitest but never used it — removed to satisfy tsc `noUnusedLocals`
- useReports.ts extended with `useCreateReport` mutation (useMutation + invalidateQueries on success)
- ReportFormPage: full form with type select, urgency select, text area, geolocation button, lat/lon fields, photo_url field, client-side validation

## Step 8 (Agent multi-select + CreateForwarding)
- STATUS: SUCCESS
- useForwardings.ts created: yes (useCreateForwarding + useUpdateForwardingStatus)
- SelectionBar.tsx created: yes (floating bar, count display, create + clear buttons)
- CreateForwardingDialog.tsx created: yes (form with institution + proposed_solution, client-side validation)
- MapPage.tsx updated: yes (showCreateDialog state, SelectionBar, CreateForwardingDialog wired)
- Tests: 14 passed (2 new CreateForwardingDialog tests + 12 pre-existing)
- Build: clean (228 modules transformed, MapPage chunk 169.77 kB)

## Step 9 (Forwardings dashboard)
- STATUS: SUCCESS
- useForwardings extended: yes (useForwardings query hook added)
- StatusSelect.tsx created: yes (inline status update via useUpdateForwardingStatus)
- ForwardingRow.tsx created: yes (expandable row with nested reports)
- ForwardingsPage.tsx replaced: yes (table with status filter, empty state, loading state)
- Tests: 16 passed (2 new StatusSelect tests + 14 pre-existing)
- Build: clean (230 modules transformed)
- Fix applied: test imported `beforeEach` from vitest but never used it — removed to satisfy tsc `noUnusedLocals`

## Step 11 (Docs + D-007)
- STATUS: SUCCESS
- CLAUDE.md updated: yes
- standards.md Frontend section updated: yes
- design-standards.md note added: yes
- conventions.md ARCHITECTURE_DESCRIPTION updated: yes
- D-007 recorded: yes (manually appended to product-design-as-intended.md — apply_marker.py refused due to file classification)
- as-coded §8 updated: yes
