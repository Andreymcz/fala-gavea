# Progress -- Plan 000105

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Codebase Patterns Found

- `CreateReport` uses constructor injection (repos passed to `__init__`), but plan specified function-level injection for `BulkCreateReports.execute()` — followed plan spec.
- Indexer pattern: `try/except` around `indexer.index(report)` with `_log.warning(...)` — same pattern used in `BulkCreateReports`.
- `IReportRepository.save()` takes a `Report` and returns `Report` — no changes needed.
- `SQLAlchemyReportTypeRepository` uses `select()` + `session.scalars()` pattern; `find_by_name` uses `.ilike()` for case-insensitive match.

## Iteration Log

### Steps 1-2 (2026-06-20)

**Status: SUCCESS**

- `Report.create()` did NOT have `created_at` param — added `created_at: datetime | None = None` with fallback to `datetime.now(UTC)`.
- `IReportRepository.save()` needed no changes — already takes a `Report` and returns `Report`.
- `find_by_name` added to `IReportTypeRepository` ABC and implemented in `SQLAlchemyReportTypeRepository` using `.ilike()`.
- `BulkCreateReports.execute()` created with function-level dependency injection as specified.
- `BulkResult` dataclass: `inserted`, `skipped`, `errors` list.
- 9 unit tests written and passing (mocks for repos/indexer).
- Commit: `13e7968`

### Steps 3-5 (2026-06-20)

**Status: SUCCESS**

- Repos/session injection: `dependencies.py` provides `get_report_repo`, `get_report_type_repo`, and `get_report_indexer` as FastAPI `Depends` functions. Routers import and use them directly via `Depends(get_*)`. No manual session handling needed in routers.
- Indexer: available as `get_report_indexer()` dependency in `dependencies.py` (lazy singleton, returns `None` if ChromaDB unavailable). Used directly in seed router via `Depends(get_report_indexer)`.
- CSV column mapping: CSV uses `texto_relato`/`latitude`/`longitude` but `BulkCreateReports` expects `descricao`/`lat`/`lon` — mapping done in router before passing rows.
- `content_type` check kept permissive (also allows `application/csv`, `application/octet-stream`) since browsers/curl vary on CSV MIME type.
- `require_role("admin")` from `dependencies.py` returns a dependency factory — used as `Depends(require_role("admin"))`.
- pyright shows 62 pre-existing errors (none introduced by new code).
- Commit: `a6bc76d`

### Step 6 (2026-06-20)

**Status: SUCCESS**

- 5 integration tests written in `tests/test_seed_endpoint.py`, all passing first run.
- Used `io.BytesIO` + `files={"file": ...}` pattern to send in-memory CSV to the test client.
- `sample_report_type` fixture (name="Iluminacao publica") reused directly — no new fixtures needed.
- Malformed CSV test: missing columns just produce empty strings (router uses `row.get(..., "")`); test verifies bad coordinates are caught and skipped gracefully.
- Missing-columns CSV test: empty `topico` yields "ReportType not found" skipped row (not a 422), so test asserts `inserted=0, skipped=1`.
- No endpoint bugs found — all behavior matched expectations from prior steps.
- Commit: `97c349f`
