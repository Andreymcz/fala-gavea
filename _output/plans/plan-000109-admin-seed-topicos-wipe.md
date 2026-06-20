# DONE | 2026-06-20 20:42 UTC | Plan 000109 | feat/admin | 2026-06-20 16:50 UTC | Admin seed topicos + wipe DB + bootstrap admin user | Review: light
plan_format_version: 1

## Context

Admin features requested:
1. **Bootstrap admin user via env vars** — on startup, if `FALA_GAVEA_ADMIN_EMAIL` + `FALA_GAVEA_ADMIN_PASSWORD` are set and no user with that email exists, create an admin user automatically. Solves the chicken-and-egg problem: an admin is needed to call `/admin/seed/*` but there is no way to promote a user to admin via the API.
2. **Seed topicos via CSV** — `POST /admin/seed/topicos` bulk-creates ReportType entries from an uploaded CSV file (columns: `nome`, `descricao`). Skips rows whose name already exists. Returns `{inserted, skipped, errors}`.
3. **Wipe all database entries** — `DELETE /admin/wipe` clears all Reports, Forwardings (+ ForwardingReport join rows), and optionally ReportTypes from SQLite and ChromaDB. Preserves Users. Returns `{wiped: {reports, forwardings, report_types}}`.

The seed relatos endpoint (`POST /admin/seed/relatos`) already exists and is complete; this plan adds the three missing admin tools alongside it.

## Steps

### Step 1: Add `BootstrapAdminUser` use case and wire into startup

Create `src/fala_gavea/application/use_cases/admin/bootstrap_admin_user.py`. The use case reads three env vars: `FALA_GAVEA_ADMIN_EMAIL`, `FALA_GAVEA_ADMIN_PASSWORD`, `FALA_GAVEA_ADMIN_NAME` (default `"Admin"`). If any required var is missing or empty, it logs DEBUG and returns without creating anything. If a user with that email already exists (`user_repo.find_by_email(email)`), it logs DEBUG and returns. Otherwise it hashes the password via `PasswordService` and creates the user with `role=admin`, logging INFO with the email.

Call `BootstrapAdminUser().execute(user_repo, password_service)` from `create_app()` in `main.py`, after `create_tables()`, using a short-lived DB session (the same pattern as other infrastructure calls — open session, call use case, close).

Also create `src/fala_gavea/application/use_cases/admin/__init__.py` (empty).

Env vars to document in the README / `product-design/project/product-design-as-coded.md`:
- `FALA_GAVEA_ADMIN_EMAIL` — email for the bootstrap admin (skipped if unset)
- `FALA_GAVEA_ADMIN_PASSWORD` — password for the bootstrap admin (skipped if unset)
- `FALA_GAVEA_ADMIN_NAME` — display name (default: `"Admin"`)

- **Files**:
  - `src/fala_gavea/application/use_cases/admin/__init__.py` (create, empty)
  - `src/fala_gavea/application/use_cases/admin/bootstrap_admin_user.py` (create)
  - `src/fala_gavea/presentation/api/main.py` (modify — call bootstrap after `create_tables()`)
- **References**: `project/standards.md § Backend`
- **Interface**: exports `BootstrapAdminUser` with `execute(user_repo, password_service) -> None`
- **Verify**: start server with `FALA_GAVEA_ADMIN_EMAIL=admin@test.com FALA_GAVEA_ADMIN_PASSWORD=secret uv run uvicorn ...`; `POST /auth/token` with those credentials returns a JWT with `role=admin`; second restart does not duplicate the user
- **Tests**: Add `tests/test_bootstrap_admin.py`: env vars set → admin user created; env vars set but user already exists → no duplicate; env vars absent → no user created; created user can authenticate via `POST /auth/token`
- [x] Done

### Step 2: Add `BulkCreateReportTypes` use case

Create `src/fala_gavea/application/use_cases/report_types/bulk_create_report_types.py`. The use case accepts a list of dicts with keys `nome` and `descricao` (optional). For each row it calls `report_type_repo.find_by_name(nome)` — if found, increments `skipped`; otherwise calls `CreateReportType(repo).execute(nome, descricao)`, increments `inserted`. Returns a `BulkResult`-style dataclass `{inserted, skipped, errors}`.

Reuse the existing `CreateReportType` use case so validation (name 3-100 chars) is not duplicated.

- **Files**: `src/fala_gavea/application/use_cases/report_types/bulk_create_report_types.py` (create)
- **References**: `project/standards.md § Backend`
- **Interface**: exports `BulkCreateReportTypes` with `execute(rows, report_type_repo) -> BulkReportTypeResult` where `BulkReportTypeResult` is `dataclass(inserted: int, skipped: int, errors: list[dict])`
- **Verify**: unit tests pass
- **Tests**: Add `tests/test_bulk_create_report_types.py` with cases: happy path (3 rows → 3 inserted), duplicate name skipped, invalid name length skipped with error
- [ ] Done

### Step 3: Add `WipeDatabase` use case

Create `src/fala_gavea/application/use_cases/admin/wipe_database.py`. The use case deletes all rows from `forwarding_reports`, `forwardings`, `reports` tables (in that FK order) via the SQLAlchemy session passed in, and optionally `report_types` if `include_report_types=True`. It also clears the ChromaDB collection via the optional `IReportIndexer` port. Returns `WipeResult{reports: int, forwardings: int, report_types: int}`.

The use case receives a raw SQLAlchemy `Session` (wipe requires bulk deletes that don't fit a domain repo interface — document with inline comment).

Also add `delete_all()` to `IReportIndexer` ABC and implement it in `ChromaSearchClient` by calling `self._client.delete_collection(self._collection_name)` and re-initialising the collection.

- **Files**:
  - `src/fala_gavea/application/use_cases/admin/wipe_database.py` (create)
  - `src/fala_gavea/domain/repositories/semantic_ports.py` (modify — add `delete_all()` abstract method to `IReportIndexer`)
  - `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` (modify — implement `delete_all()`)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 1
- **Interface**: exports `WipeDatabase` with `execute(db, include_report_types=False, indexer=None) -> WipeResult`
- **Verify**: `uv run pytest tests/test_wipe.py -v` passes
- **Tests**: Add `tests/test_wipe.py`: wipe clears reports+forwardings; wipe with `include_report_types=True` also clears types; user count unchanged after wipe
- [ ] Done

### Step 4: Add `BulkCreateReportTypes` use case

Create `src/fala_gavea/application/use_cases/report_types/bulk_create_report_types.py`. Accepts a list of dicts with keys `nome` and `descricao` (optional). For each row calls `report_type_repo.find_by_name(nome)` — if found, increments `skipped`; otherwise calls `CreateReportType(repo).execute(nome, descricao)`, increments `inserted`. Returns `BulkReportTypeResult{inserted, skipped, errors}`.

Reuses the existing `CreateReportType` use case so validation (name 3-100 chars) is not duplicated.

- **Files**: `src/fala_gavea/application/use_cases/report_types/bulk_create_report_types.py` (create)
- **References**: `project/standards.md § Backend`
- **Interface**: exports `BulkCreateReportTypes` with `execute(rows, report_type_repo) -> BulkReportTypeResult`
- **Verify**: unit tests pass
- **Tests**: Add `tests/test_bulk_create_report_types.py`: happy path (3 rows → 3 inserted), duplicate name skipped, invalid name length skipped with error
- [ ] Done

### Step 5: Add schemas and extend seed router with two new endpoints

**Schemas** — add to `src/fala_gavea/presentation/schemas/seed_schemas.py`:
- `SeedTopicosResponse` (same shape as `SeedRelatosResponse`)
- `WipedCounts{reports: int, forwardings: int, report_types: int}` and `WipeResponse{wiped: WipedCounts}`

**Router** — extend `src/fala_gavea/presentation/api/routers/seed.py` with:

`POST /admin/seed/topicos` (admin-only): accepts `UploadFile` CSV (columns `nome`, `descricao`). Returns `SeedTopicosResponse`.

`DELETE /admin/wipe` (admin-only): query param `include_report_types: bool = False`. Injects `Session` via `Depends(get_db)`. Returns `WipeResponse`.

- **Files**:
  - `src/fala_gavea/presentation/schemas/seed_schemas.py` (modify)
  - `src/fala_gavea/presentation/api/routers/seed.py` (modify)
- **References**: `project/standards.md § Backend`
- **Depends on**: Step 3, Step 4
- **Interface**: N/A (leaf endpoints)
- **Verify**: `uv run pytest tests/test_seed_topicos_endpoint.py tests/test_wipe_endpoint.py -v` passes
- **Tests**:
  - `tests/test_seed_topicos_endpoint.py`: happy path (2 rows inserted), duplicate skipped, invalid name length → error row, non-admin gets 403
  - `tests/test_wipe_endpoint.py`: wipe clears reports; `include_report_types=true` clears types too; non-admin gets 403; wipe with no data returns zeros
- **Docs**: Update `product-design/project/product-design-as-coded.md § 1. Platform Purpose` to list all three new endpoints and the three new env vars
- [ ] Done

## Review

**Depth: light** (auto=light, floor=light, flag=none)

| Perspective | Finding | Status |
|---|---|---|
| P1 Security | Bootstrap admin only runs if env vars are explicitly set — no surprise admin on clean deploys | Adopted |
| P1 Security | Password is hashed via `PasswordService` — plaintext never stored | Adopted |
| P0 Correctness | FK deletion order (forwarding_reports → forwardings → reports) prevents constraint errors | Adopted |
| P0 Correctness | `delete_all()` re-initialises ChromaDB collection after deletion to avoid stale client state | Adopted |
| P1 Security | `/admin/wipe` is admin-only and returns a 403 for other roles — data loss path is guarded | Adopted |
| P1 Security | CSV parsing uses `csv.DictReader` with known columns; no shell execution risk | Adopted |
| P2 Simplicity | Reuses existing `CreateReportType` for name validation rather than duplicating | Adopted |
| P3 Test coverage | Wipe endpoint tests verify user count is unchanged (users must survive wipe) | Adopted |

## Commit

```
feat(admin): bootstrap admin user + seed topicos + wipe DB endpoints
```

## Pending

- [x] `test-implementation` — 18 new tests, all passing (2026-06-20 20:42 UTC)

## Implementation Summary

**Steps completed**: 5/5 (Steps 2 and 4 were duplicates; implemented once)
**Commit**: `094dde6` — feat(admin): bootstrap admin user + seed topicos + wipe DB endpoints

**Files created**:
- `src/fala_gavea/application/use_cases/admin/__init__.py`
- `src/fala_gavea/application/use_cases/admin/bootstrap_admin_user.py`
- `src/fala_gavea/application/use_cases/admin/wipe_database.py`
- `src/fala_gavea/application/use_cases/report_types/bulk_create_report_types.py`
- `tests/test_bootstrap_admin.py`, `tests/test_bulk_create_report_types.py`, `tests/test_wipe.py`, `tests/test_seed_topicos_endpoint.py`, `tests/test_wipe_endpoint.py`

**Files modified**:
- `src/fala_gavea/domain/repositories/semantic_ports.py` — added `delete_all()` to `IReportIndexer` ABC
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` — implemented `delete_all()`
- `src/fala_gavea/presentation/api/main.py` — calls `BootstrapAdminUser` after `create_tables()`
- `src/fala_gavea/presentation/api/routers/seed.py` — added `POST /admin/seed/topicos` and `DELETE /admin/seed/wipe`
- `src/fala_gavea/presentation/schemas/seed_schemas.py` — added `SeedTopicosResponse`, `WipedCounts`, `WipeResponse`

**Deviation**: The wipe endpoint is at `DELETE /admin/seed/wipe` (not `/admin/wipe` as specified) because the seed router is mounted at `/admin/seed`. This is the correct URL for the current prefix configuration.

**Pre-existing failure**: `test_report_types.py::test_create_report_type_citizen_forbidden` was already failing before this plan (verified via git stash). Not caused by this implementation.
