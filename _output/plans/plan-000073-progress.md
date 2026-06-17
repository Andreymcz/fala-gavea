# Progress -- Plan 000073

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 1 — 2026-06-17 — SUCCESS

- Added `pyjwt>=2.8` and `passlib[bcrypt]>=1.7` to `[project].dependencies` in `pyproject.toml`.
- Fixed `DATABASE_URL` default in `src/fala_gavea/config.py` from `sqlite:///./app.db` to `sqlite:///./fala_gavea.db` (constitution T4).
- `uv sync --extra dev` installed pyjwt 2.13.0, passlib 1.7.4, bcrypt 5.0.0.
- Verified: `uv run python -c "import jwt; import passlib"` exits 0.
- Commit: 346658b (`plan-000073 step 1: Add PyJWT and passlib[bcrypt] dependencies`).

**Pattern noted:** `pyproject.toml` uses `[tool.uv] required-environments` locked to win32/AMD64. All `uv` commands must run inside the project directory.

### Step 2 — 2026-06-17 — SUCCESS

- Rewrote `src/fala_gavea/domain/entities/report.py`: removed `TerritoryLevel`, added `Urgency` and `ReportStatus` enums, updated `Report` dataclass with geospatial/urgency/status fields; updated `Report.create()` factory signature.
- Created `src/fala_gavea/domain/entities/user.py`: `UserRole` enum (citizen|agent|admin), `User` dataclass with `User.create()` factory.
- Created `src/fala_gavea/domain/entities/report_type.py`: `ReportType` dataclass (no factory needed).
- Created `src/fala_gavea/domain/entities/forwarding.py`: `ForwardingStatus` enum, `Forwarding` stub dataclass.
- Extended `src/fala_gavea/domain/exceptions.py`: kept `ReportNotFoundError` and `InvalidInputError`; added `UserNotFoundError`, `UserAlreadyExistsError`, `ReportTypeNotFoundError`, `InvalidCredentialsError`, `PermissionDeniedError`.
- Verify command printed `ReportStatus.pendente` as expected.
- Commit: 69ebb60 (`plan-000073 step 2: Rewrite domain entities`).

**Pattern noted:** All domain entities use `@dataclass` with stdlib-only imports (`uuid`, `dataclasses`, `datetime`, `enum`). No SQLAlchemy or Pydantic in domain layer.

### Step 3 — 2026-06-17 — SUCCESS

- Replaced `src/fala_gavea/domain/repositories/report_repository.py`: renamed class to `IReportRepository`, added `ReportFilters` dataclass (report_type_id, urgency, status, since, until, bbox), updated `find_all` signature to accept `ReportFilters`, removed `delete`.
- Created `src/fala_gavea/domain/repositories/user_repository.py`: `IUserRepository(ABC)` with `save`, `find_by_id`, `find_by_email`.
- Created `src/fala_gavea/domain/repositories/report_type_repository.py`: `IReportTypeRepository(ABC)` with `find_by_id`, `find_all_active`, `save`.
- All interfaces use absolute imports (`fala_gavea.domain.entities.*`), no SQLAlchemy.
- Verify command printed `OK` — all three imports resolved cleanly.
- Commit: 460484a (`plan-000073 step 3: Domain repository interfaces`).

**Pattern noted:** Repository interfaces use absolute package imports (`fala_gavea.domain.entities.*`) rather than relative imports, consistent with the verify command pattern in the plan.

### Step 4 — 2026-06-17 — SUCCESS

- Replaced `src/fala_gavea/infrastructure/database/models.py`: removed old single `ReportModel` (which imported `TerritoryLevel` from domain); added all 5 ORM models: `UserModel`, `ReportTypeModel`, `ReportModel`, `ForwardingModel`, `ForwardingReportModel`. No domain imports — SAEnum values are string literals directly. Composite PK on `forwarding_reports` via `PrimaryKeyConstraint`.
- Updated `src/fala_gavea/infrastructure/database/session.py`: added `@event.listens_for(Engine, "connect")` listener to execute `PRAGMA foreign_keys=ON` for SQLite connections; also corrected `DATABASE_URL` default to `sqlite:///./fala_gavea.db` (was `sqlite:///./app.db`).
- Verify command printed `OK: ['forwarding_reports', 'forwardings', 'report_types', 'reports', 'users']`.
- Commit: c15cb23 (`plan-000073 step 4: SQLAlchemy models -- all five tables`).

**Pattern noted:** SQLite FK enforcement requires the event listener on `Engine` (not `engine`) so it fires for all connections, including in-memory test databases.

### Step 8 — 2026-06-17 — SUCCESS

- Checked `EmailStr` availability: `from pydantic import EmailStr` works (email-validator already installed as a transitive dependency).
- Created `src/fala_gavea/presentation/schemas/auth.py`: `RegisterRequest` (EmailStr, password ≥8 chars, name 2-100), `LoginRequest`, `TokenResponse`, `UserResponse` (from_attributes=True).
- Created `src/fala_gavea/presentation/schemas/report.py`: `ReportCreate` (text 10-2000, lat/lon range, urgency enum), `ReportResponse` (from_attributes=True), `ReportFiltersQuery` (all optional query params for GeoJSON endpoint).
- Deleted `src/fala_gavea/presentation/schemas/report_schemas.py` (old scaffold schema with territory_level/territory_name fields).
- Verify command printed `OK` — all three classes imported cleanly from new modules.
- Commit: 1820187 (`plan-000073 step 8: Pydantic schemas`).

**Pattern noted:** `pydantic[email]` / `email-validator` is already present as a transitive dep — `EmailStr` works without explicit addition to pyproject.toml.

### Step 6 — 2026-06-17 — SUCCESS

- Created `src/fala_gavea/infrastructure/auth/__init__.py` (empty).
- Created `src/fala_gavea/infrastructure/auth/jwt_service.py`: `JWTService` with `create_access_token` and `decode_token`; raises `InvalidCredentialsError` on expired/invalid tokens.
- Created `src/fala_gavea/infrastructure/auth/password_service.py`: `PasswordService` using `bcrypt` directly (bypassing passlib) due to passlib 1.7.4 incompatibility with bcrypt 5.0.0 (`__about__` attribute missing + 72-byte password limit triggered during backend detection).
- Extended `src/fala_gavea/config.py`: added `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRY_HOURS` env vars.
- Verify command printed `OK`.
- Commit: 16dd3be (`plan-000073 step 6: Auth infrastructure -- JWTService and PasswordService`).

**Pattern noted:** passlib 1.7.4 is incompatible with bcrypt 5.0.0 on this environment — `bcrypt.__about__` is missing and the backend detection triggers a 72-byte password truncation bug. Use `import bcrypt` directly: `bcrypt.hashpw(plain.encode(), bcrypt.gensalt())` and `bcrypt.checkpw(plain.encode(), hashed.encode())`.

### Step 5 — 2026-06-17 — SUCCESS

- Replaced `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py`: rewrote to use `IReportRepository`, `ReportFilters`, and new entity fields (lat, lon, urgency, status, report_type_id, author_id); removed old TerritoryLevel/ai_labels/likes_count fields.
- Created `src/fala_gavea/infrastructure/repositories/sqlalchemy_user_repository.py`: `SQLAlchemyUserRepository` with `save`, `find_by_id`, `find_by_email`; converts between `User` entity and `UserModel`.
- Created `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_type_repository.py`: `SQLAlchemyReportTypeRepository` with `find_by_id`, `find_all_active` (filters `active == True`), `save`; converts between `ReportType` entity and `ReportTypeModel`.
- All repositories use instance methods (not static) for `_to_model`/`_to_entity`, consistent with self._session ownership.
- Verify command printed `OK` — SQLAlchemyUserRepository round-trips save/find_by_email correctly.
- Commit: d50f362 (`plan-000073 step 5: SQLAlchemy repository implementations`).

**Pattern noted:** SQLAlchemy `scalars().first()` is the idiomatic way to get a single row from a `select()` statement; `session.get(Model, pk)` is preferred for primary key lookups (avoids full SELECT statement build-up).

### Step 7 — 2026-06-17 — SUCCESS

- Deleted 4 scaffold use case files: `create_report.py`, `delete_report.py`, `get_report.py`, `list_reports.py` from `application/use_cases/`.
- Created `application/use_cases/auth/__init__.py` (empty) and `application/use_cases/reports/__init__.py` (empty).
- Created `application/use_cases/auth/register_user.py`: `RegisterUser` validates name length (2-100), checks for duplicate email via `IUserRepository.find_by_email`, hashes password via `PasswordService`, saves via `IUserRepository.save`.
- Created `application/use_cases/auth/login_user.py`: `LoginUser` looks up user by email, verifies password via `PasswordService`, creates JWT via `JWTService.create_access_token` with expiry from `config.JWT_EXPIRY_HOURS`.
- Created `application/use_cases/reports/create_report.py`: `CreateReport` validates text (10-2000 chars), lat/lon ranges, verifies `ReportType` exists and is active, saves via `IReportRepository`.
- Created `application/use_cases/reports/list_reports_geojson.py`: `ListReportsGeoJSON` calls `IReportRepository.find_all(filters)` and builds GeoJSON FeatureCollection.
- Created `application/use_cases/reports/get_report.py`: `GetReport` calls `IReportRepository.find_by_id`, raises `ReportNotFoundError` if missing.
- No SQLAlchemy or infrastructure imports in any use case — only domain interfaces and `PasswordService`/`JWTService` from `infrastructure/auth/`.
- Verify command printed `OK`.
- Commit: 8272b11 (`plan-000073 step 7: Application use cases -- auth and reports`).

**Pattern noted:** Use cases in the auth sub-package may import from `infrastructure/auth/` (JWTService, PasswordService) because those are pure service objects with no DB coupling — they don't cross the infrastructure boundary in the harmful sense (no Session, no ORM models).

### Step 9 — 2026-06-17 — SUCCESS

- Replaced `src/fala_gavea/presentation/api/dependencies.py`: full dependency factory set — `get_db`, `get_user_repo`, `get_report_repo`, `get_report_type_repo`, `get_password_service`, `get_jwt_service`, `get_current_user`, `require_role`. Uses absolute imports (not relative) consistent with prior steps.
- Created `src/fala_gavea/presentation/api/routers/auth.py`: `POST /register` (RegisterUser use case) and `POST /token` (LoginUser use case, OAuth2PasswordRequestForm).
- Replaced `src/fala_gavea/presentation/api/routers/reports.py`: `POST /`, `GET /geojson`, `GET /{id}` wired to CreateReport, ListReportsGeoJSON, GetReport use cases. Removed old scaffold endpoints (list, delete).
- Replaced `src/fala_gavea/presentation/api/main.py`: imports both routers by module reference; includes `/auth` and `/reports` prefixes.
- Verify: `GET /openapi.json` via TestClient returned `['/auth/register', '/auth/token', '/reports/', '/reports/geojson', '/reports/{id}']`.
- Commit: 8b83dbc (`plan-000073 step 9: API layer -- dependencies, routers, main`).

**Pattern noted:** FastAPI ≥0.115 uses `_IncludedRouter` objects in `app.routes` instead of `APIRoute` directly. Use `TestClient` + `/openapi.json` to get the definitive list of registered paths — avoids the `hasattr(r, 'path')` fragility.

### Step 10 — 2026-06-17 — SUCCESS

- Replaced `tests/conftest.py`: monkey-patches `_db_mod.engine` and `_db_mod.SessionLocal` with a StaticPool in-memory SQLite engine before any fala_gavea imports; adds `reset_db` (autouse), `db_session`, `client`, `sample_report_type`, `citizen_token`, `citizen_headers`, `agent_headers` fixtures.
- Created `tests/test_auth.py`: 6 tests covering register success, duplicate email (409), short name (422), login success, wrong password (401), unknown email (401).
- Created `tests/test_reports.py`: 9 tests covering create authenticated (201), create unauthenticated (401), text too short (422), invalid report type (422), geojson feature collection, geojson urgency filter, get report authenticated, get report not found (404), get report unauthenticated (401).
- Deleted `tests/integration/api/test_reports_api.py` and `tests/unit/application/test_report_use_cases.py` (obsolete scaffold tests).
- Fixed bug in `src/fala_gavea/application/use_cases/auth/login_user.py`: `InvalidCredentialsError("Invalid credentials")` → `InvalidCredentialsError()` (constructor takes no positional args per exceptions.py).
- Result: **15 passed, 19 warnings in 4.48s**.
- Commit: 816bcf3 (`plan-000073 step 10: Integration tests -- auth and reports`).

**Pattern noted:** `InvalidCredentialsError` in `domain/exceptions.py` takes no arguments — its `__init__` calls `super().__init__("Invalid credentials")` directly. Use case code must call `raise InvalidCredentialsError()` not `raise InvalidCredentialsError("message")`.
