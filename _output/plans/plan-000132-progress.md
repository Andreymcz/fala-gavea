# Progress -- Plan 000132

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 3 — 2026-06-21

Added `rank(query, ids) -> dict[str, float]` abstract method to `ISemanticSearchPort` in `semantic_ports.py`. Implemented in `ChromaSearchClient`: embeds query with `_encode_query`, fetches stored embeddings via `collection.get(ids=ids, include=["embeddings"])`, computes cosine similarity manually (dot product / product of norms), clamps to [0,1]. Formula is pure cosine (not the `1/(1+dist)` used in `search()`/`similar()` which convert L2 distance — `rank()` operates on arbitrary candidate sets without querying ChromaDB's ANN index). Pyright: 65 errors (all pre-existing, none introduced by these changes).

### Step 1 — 2026-06-21

Extended `ReportFilters` in `domain/repositories/report_repository.py`: replaced single-value `report_type_id`, `urgency`, `status` with plural list fields (`report_type_ids`, `urgencies`, `statuses`); added `text: str | None = None`. Added `find_page` abstract method. Updated `SQLAlchemyReportRepository.find_all` to use `.in_()` and `.ilike()`, and implemented `find_page` with count subquery + offset/limit. Updated two `ReportFilters(...)` constructors in `reports.py` router (wrapping single values in lists). Pyright: 65 pre-existing errors, none introduced by this step. Gotcha: `find_page` also needed a concrete implementation to satisfy abstract class; the import of `func`/`desc` was moved inside the method to avoid polluting module scope.

### Step 4 — 2026-06-21

Created `QueryReports` use case at `src/fala_gavea/application/use_cases/reports/query_reports.py`. Two paths: semantic (q + search_port → filter SQL with order="none"/candidate_cap → rank in memory → sort desc by score → paginate slice) and recency (find_page with order="recent"). Returns `QueryPage(items, total, limit, offset, ranked_by)`. Tests in `tests/test_query_reports.py` cover: score ordering, pagination slicing, recency fallback (no q), search_port=None fallback, max_results cap. All 5 tests pass. Pyright: 66 pre-existing errors, none from this step.

### Step 2 — 2026-06-21

Created `tests/test_report_repository.py` with 7 unit tests covering: `find_all` urgencies IN filter (alta+media excludes baixa), `find_all` report_type_ids IN filter, `find_all` text ilike case-insensitive, `find_page` recent order with correct total, `find_page` offset pagination, `candidate_cap` limiting rows when cap < limit, and no-cap-effect when rows < cap. All 7 tests pass. No new lint errors introduced in the new file.

### Step 5 — 2026-06-21

Added `ReportQueryRequest`, `ReportQueryItem`, `ReportQueryResponse` schemas to `presentation/schemas/report.py` (imports `Urgency`/`ReportStatus` for validators). Added `POST /reports/query` route to `reports.py` router near `/search`; imports `QueryReports`. Route parses bbox from string, builds `ReportFilters`, delegates to `QueryReports.execute`, returns paginated envelope. Created `tests/test_reports_query_api.py` with 6 tests (urgency filter, bad enum 422, unauthenticated 401, pagination envelope, empty filters, recency ranked_by). All 6 pass. No new ruff or pyright errors.

### Step 8 — 2026-06-21
Added cross-reference dependency note to plan-000131: FilterPanel/views now read through `POST /reports/query` (plan-000132); `useFilteredReports`/`useSemanticSearch` retargeted in Step 7; R2 catch-all guard remains independent.
