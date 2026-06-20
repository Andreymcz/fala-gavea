# DONE | 2026-06-20 16:55 UTC | Plan 000105 | feat/reports | 2026-06-19 21:53 UTC | CSV seed relatos API endpoint + bulk insert use case | Review: light
plan_format_version: 1

## Brief

Create an API endpoint to receive a CSV file with seed relatos. The use case will bulk-insert reports into SQLite (and optionally index them into ChromaDB).

---

## Context

- Existing CSV schema: `seeds/relatos/SCHEMA.md` — columns: `id_cidadao`, `texto_relato`, `latitude`, `longitude`, `data`, `topico`
- `scripts/seed_relatos.py` reads CSVs and calls the REST API one-by-one (HTTP); the new endpoint accepts the CSV directly, resolves report_type by topic name, and inserts via `IReportRepository.save()` in bulk
- `CreateReport` use case validates one report at a time; the new use case (`BulkCreateReports`) re-uses the same validation path but batches DB commits
- Endpoint must be admin-only (only admins seed the corpus)
- ChromaDB indexing: best-effort per row (skip indexer failures, log warning — same pattern as `CreateReport`)
- Return: `{inserted: N, skipped: N, errors: [{row, reason}]}`

---

## Files Created / Modified

| File | Action |
|------|--------|
| `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py` | **Create** |
| `src/fala_gavea/presentation/schemas/seed_schemas.py` | **Create** |
| `src/fala_gavea/presentation/api/routers/seed.py` | **Create** |
| `src/fala_gavea/presentation/api/main.py` | **Modify** — include seed router |
| `tests/test_seed_endpoint.py` | **Create** |

---

## Steps

### Step 1 — `BulkCreateReports` use case
**File:** `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py`

Create a new use case class that:
- Accepts: `rows: list[dict]`, `author_id: str`, `report_type_repo: IReportTypeRepository`, `report_repo: IReportRepository`, `indexer: IReportIndexer | None`
- Resolves `report_type_id` from `topico` name via `report_type_repo.find_by_name()` — if not found, record a skip
- For each valid row: calls `Report.create(text, lat, lon, Urgency("media"), report_type_id, author_id)`, then `report_repo.save(report)`
- After save, calls `indexer.index(report)` in try/except (same pattern as `CreateReport`)
- Returns `BulkResult(inserted=N, skipped=N, errors=[{row, reason}])`
- **No** batch commit tricks — each `save()` commits normally; the session is per-request

> Note: `IReportRepository` has no `find_by_name` for ReportType — we need to add `find_by_name` to `IReportTypeRepository` and its SQLAlchemy implementation.

### Step 2 — `find_by_name` on ReportType repository
**Files:**
- `src/fala_gavea/domain/repositories/report_type_repository.py` — add `find_by_name(name: str) -> ReportType | None`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_type_repository.py` — implement with case-insensitive match

### Step 3 — Pydantic response schema
**File:** `src/fala_gavea/presentation/schemas/seed_schemas.py`

```python
class SeedErrorItem(BaseModel):
    row: int
    reason: str

class SeedRelatosResponse(BaseModel):
    inserted: int
    skipped: int
    errors: list[SeedErrorItem]
```

### Step 4 — `POST /admin/seed/relatos` router
**File:** `src/fala_gavea/presentation/api/routers/seed.py`

- Accepts `file: UploadFile` (content_type `text/csv`)
- Auth: `require_role("admin")`
- Parses CSV with `csv.DictReader` from the uploaded bytes (UTF-8)
- Maps columns to dict keys matching the schema: `id_cidadao`, `texto_relato`, `latitude`, `longitude`, `data`, `topico`
- Resolves `author_id` from `id_cidadao` via `user_repo.find_by_email_or_id()` — fallback: use the authenticated admin's id if citizen not found (log warning)
- Calls `BulkCreateReports(...).execute(rows, author_id=...)`
- Returns `SeedRelatosResponse`

**Auth note:** `require_role("admin")` already exists in `dependencies.py`.

### Step 5 — Wire router into `main.py`
**File:** `src/fala_gavea/presentation/api/main.py`

Add:
```python
from fala_gavea.presentation.api.routers.seed import router as seed_router
app.include_router(seed_router, prefix="/admin/seed", tags=["seed"])
```

### Step 6 — Tests
**File:** `tests/test_seed_endpoint.py`

- Happy path: upload a 3-row CSV, assert `inserted=3`
- Unknown topico: one row with invalid topic → `skipped=1`, `errors` contains that row
- Malformed CSV (missing columns): returns 422
- Non-admin caller: returns 403

Use existing `conftest.py` patterns (in-memory SQLite, test client, admin token fixture).

---

## Constraints & Decisions

- **No urgency column in CSV** — defaults to `"media"` for all seed rows (same as `seed_relatos.py`); urgency is for citizen-submitted reports, not seed data
- **`data` column** — parsed as `datetime` and stored as `created_at` override; `Report.create()` sets `created_at=datetime.now()` so we need a `created_at` override param — add optional `created_at: datetime | None = None` to `Report.create()` and `IReportRepository.save()`
- **Idempotency** — no deduplication; re-uploading the same CSV inserts duplicates (acceptable for seed data)
- **Size limit** — FastAPI default 1 MB file limit is fine for seed CSVs; no explicit override needed
- **Semantic indexing** — same best-effort pattern as `CreateReport`; large CSV uploads will be slower while indexing runs synchronously per row (acceptable for admin-only seed flow)

---

## Docs

- Update `product-design/project/product-design-as-coded.md` §1 (Platform Purpose) to mention `POST /admin/seed/relatos` endpoint

---

## Implementation Summary

**Completed:** 6/6 steps | **Iterations:** 3 subagents + 1 in-context fix | **Commits:** 13e7968, a6bc76d, 97c349f, 4f6fdf2

### What was built
- `BulkCreateReports` use case with `BulkResult` dataclass (inserted/skipped/errors)
- `find_by_name` (case-insensitive) added to `IReportTypeRepository` ABC and `SQLAlchemyReportTypeRepository`
- `Report.create()` extended with optional `created_at: datetime | None` param
- `SeedErrorItem` + `SeedRelatosResponse` Pydantic schemas
- `POST /admin/seed/relatos` endpoint (admin-only, CSV upload, bulk insert)
- Router wired into `main.py` under `/admin/seed` prefix
- 14 tests (9 unit + 5 integration), all passing

### Review fixes applied
- Naive datetime → always UTC-aware when parsing ISO strings from CSV `data` column
- `topico` whitespace stripped before `find_by_name` lookup
- Test name `_returns_422` corrected to `_returns_200_all_skipped`

### Deferred (advisory)
- File-size limit on upload (admin-only endpoint, low practical risk)
- HTTP 207 vs 200 on partial failures
- Lat/lon range validation
- Empty `text` guard
