# QA Log | Plan 000073 | 2026-06-17 21:17 UTC | Wave 0 Item 1 — Domain, Auth, Reports

**Brief**: Implementation session for plan-000073 (fala-gavea Wave 0 Item 1): domain entities, JWT auth, report CRUD, GeoJSON endpoint, and integration tests — full 10-step execution via auto-mode subagents.

---

## Q1

`/plan roadmap 1 item 1 complete`

## A1

Pre-skill ran, reserved plan ID 000073, generated plan `plan-000073-feature-b-wave-0-item-1-domain-auth-reports.md` covering 10 implementation steps across domain entities, repository interfaces, SQLAlchemy models, auth infrastructure (JWT + bcrypt), Pydantic schemas, use cases, API layer, and integration tests. Plan presented for user approval.

---

## Q2

User selected: "Implement now" — chose to immediately execute plan-000073.

## A2

`/implement plan-000073` launched in auto mode. 10 steps executed via fresh subagents in dependency order (1→2→3→4→8→6→5→7→9→10). All steps passed.

Key implementation decisions made during execution:
- **passlib incompatibility**: passlib 1.7.4 is incompatible with bcrypt 5.0.0 on this environment (`__about__` attribute missing, 72-byte truncation bug triggered during backend detection). PasswordService rewritten to use `import bcrypt` directly.
- **InvalidCredentialsError constructor**: Takes no positional args — `raise InvalidCredentialsError()` (not `raise InvalidCredentialsError("message")`).
- **JWT_SECRET_KEY in tests**: Set via `os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"` at top of conftest.py before any fala_gavea imports.
- **agent_headers fixture**: Inserts user with role=agent directly via SQLAlchemyUserRepository (POST /auth/register always creates citizen).
- **StaticPool**: In-memory SQLite for tests uses `connect_args={"check_same_thread": False}, poolclass=StaticPool`.

Final test result: **15 passed, 19 warnings in 4.48s** (6 auth tests + 9 report tests).

Files created/modified across 10 commits:
- `pyproject.toml` — added pyjwt, passlib[bcrypt] deps
- `src/fala_gavea/config.py` — JWT env vars, DATABASE_URL fix
- `src/fala_gavea/domain/entities/` — user.py, report.py (rewritten), report_type.py, forwarding.py
- `src/fala_gavea/domain/repositories/` — user_repository.py, report_repository.py (rewritten), report_type_repository.py
- `src/fala_gavea/domain/exceptions.py` — 5 new exception types
- `src/fala_gavea/infrastructure/database/models.py` — 5 ORM models
- `src/fala_gavea/infrastructure/database/session.py` — PRAGMA foreign_keys=ON listener
- `src/fala_gavea/infrastructure/auth/` — jwt_service.py, password_service.py
- `src/fala_gavea/infrastructure/repositories/` — sqlalchemy_user_repository.py, sqlalchemy_report_type_repository.py, sqlalchemy_report_repository.py (rewritten)
- `src/fala_gavea/application/use_cases/auth/` — register_user.py, login_user.py
- `src/fala_gavea/application/use_cases/reports/` — create_report.py, list_reports_geojson.py, get_report.py
- `src/fala_gavea/presentation/schemas/` — auth.py, report.py
- `src/fala_gavea/presentation/api/dependencies.py` — full rewrite
- `src/fala_gavea/presentation/api/routers/` — auth.py, reports.py
- `src/fala_gavea/presentation/api/main.py` — routers registered
- `tests/conftest.py` — StaticPool fixtures
- `tests/test_auth.py` — 6 tests
- `tests/test_reports.py` — 9 tests
- Deleted: 4 scaffold use cases, report_schemas.py, 2 scaffold test files

---

## Q3

User selected: "Apply now" — apply STATUS:implemented markers for §2 Entity Hierarchy, §4 Permission Model, §5 Content Authoring, §6 Export (GeoJSON), §10 Validation Constants.

## A3

`apply_marker.py` ran but failed: script requires `--id ENTRY_ID` (a specific marker entry ID within the file) in addition to `--target`. Entry IDs for the candidate sections were not known at the time. Action deferred to pending entry pa-000007 (`mark-implemented` type).

Pending actions filed during post-skill:
- **pa-000005** (verify-as-coded): Review product-design-as-coded.md against real implementation of plan-000073
- **pa-000006** (update-documentation): Run `/document --plan plan-000073`
- **pa-000007** (mark-implemented): Flip STATUS markers on product-design-as-intended.md for §2, §4, §5, §6, §10

---

## Q4

*(Session continuation after context compaction)* — post-skill resumed from step 3 (QA log generation).

## A4

Post-skill continuing from step 3 onward. Generating QA log, then proceeding to commit message, git safety check, index regeneration, and final commit.

