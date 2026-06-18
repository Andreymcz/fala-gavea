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
