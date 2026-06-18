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
