# DONE | 2026-06-21 18:39 UTC | Plan 000132 | REDESIGN-B | 2026-06-21 18:13 UTC | Unified reports query API (Phase B) | Review: standard
plan_format_version: 1

source: research-000130 -- unified POST /reports/query (multi-value + bbox + date range + semantic ranker + pagination); NL assistant (Phase A) + saved filters (Phase C) deferred

## User brief

Build **Phase B** of research-000130: a single unified query endpoint on `/reports` that combines all search parameters in one request, and retarget the research-000129 front-end data layer onto it.

- **Unified `POST /reports/query`**: multi-value structured filters (`report_type_ids[]`, `urgencies[]`, `statuses[]`), `bbox`, date range (`since`/`until`), an optional literal `text` substring filter, an optional semantic `q` that **ranks** the filtered set by similarity, plus `limit`/`offset` pagination and a `max_results` cap.
- **SQL is the filter source of truth; ChromaDB is a ranker only.** Filter in SQL (multi-value `IN`, bbox, dates, text `LIKE`) -> cap at `max_results` -> if `q` present, rank the whole filtered candidate set in memory by semantic similarity -> else order by `created_at desc` -> slice `[offset:offset+limit]`. Do **not** mirror `status`/`created_at` into Chroma metadata.
- **Additive**: keep `/reports/geojson` and `/reports/search` working until the SPA fully migrates.
- **Frontend retarget (research-000129 consumes Phase B)**: `api.ts` + the `useFilteredReports`/`useSemanticSearch` hooks call the unified endpoint and adapt its rows into the existing features/count shape so plan-000131's FilterPanel/Map/Table UI keeps working unchanged.
- **Deferred** (not in this plan): Phase A NL-to-filter assistant; Phase C per-user saved filters.

## Agent interpretation

A backend-led increment with a thin frontend integration. The architectural spine is a new `QueryReports` use case that orchestrates **filter (SQL) -> rank (Chroma, optional) -> paginate**, leaving SQL authoritative for filtering and Chroma a pure ranker (per research-000130 F1/F2). To avoid two filter models, extend the existing `ReportFilters` to multi-value lists + a `text` field (single source of truth) and adapt the two legacy call sites (`/reports/geojson`, `/reports/keywords`) to wrap their single-valued query params into singletons — a small, well-tested blast radius. Pagination is computed over the **fully-ranked** candidate set (never over Chroma's top-n), so pages are deterministic. The endpoint returns flat report rows + optional score in a `{ items, total, limit, offset, ranked_by }` envelope; the frontend hook maps rows into the GeoJSON-features/count shape that plan-000131's views already read, so no view component changes are required here. This is intentionally the **smallest shippable foundation** that A and C will later build on.

**Co-design note:** this plan sits *under* the committed plan-000131 (research-000129 front-end). plan-000131's UI (staged draft/Apply, chips, presets, table, map) is unchanged; only the data layer beneath it retargets. A cross-reference dependency is added to plan-000131 (Step 8).

---

## Steps

### Step 1: Extend `ReportFilters` to multi-value + text (domain)
Widen the canonical filter dataclass in `src/fala_gavea/domain/repositories/report_repository.py`:
- Replace `report_type_id: str | None` -> `report_type_ids: list[str] | None`; `urgency: Urgency | None` -> `urgencies: list[Urgency] | None`; `status: ReportStatus | None` -> `statuses: list[ReportStatus] | None`. Keep `since`, `until`, `bbox`.
- Add `text: str | None = None` (case-insensitive substring over `Report.text`).
- Add a new `find_page` abstract method to `IReportRepository`: `find_page(self, filters: ReportFilters, *, limit: int, offset: int, order: str = "recent", candidate_cap: int = 500) -> tuple[list[Report], int]` returning `(rows, total)`. Keep `find_all(filters)` (used by legacy/keywords paths) — it now reads the plural fields.
- **Files**: `src/fala_gavea/domain/repositories/report_repository.py` (modify)
- **References**: `product-design/conventions.md`
- **Interface**: `ReportFilters(report_type_ids, urgencies, statuses, since, until, bbox, text)`; `IReportRepository.find_all(filters)`, `find_page(filters, *, limit, offset, order, candidate_cap)`.
- **Verify**: `uv run pyright src/` clean.
- **Tests**: covered via repository tests in Step 2.

### Step 2: SQLAlchemy repo — multi-value `IN`, text `LIKE`, sort + pagination
Update `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py`:
- `find_all`: switch the WHERE builders to lists — `report_type_id.in_(filters.report_type_ids)`, `urgency.in_([u.value for u in filters.urgencies])`, `status.in_([s.value for s in filters.statuses])` (each guarded by `is not None and len > 0`); keep since/until/bbox; add `text` -> `ReportModel.text.ilike(f"%{filters.text}%")`.
- Add `find_page(filters, *, limit, offset, order, candidate_cap)`: build the same filtered `select`, compute `total` via `select(func.count()).select_from(subquery)` (or `len` of capped ids), apply ordering (`order == "recent"` -> `created_at desc`; otherwise leave insertion order for caller-side ranking), apply `candidate_cap` as a safety `.limit(candidate_cap)` when no semantic ranking is requested, then apply `offset`/`limit`. When the caller will rank in memory (semantic path), `find_page` is called with `order="none"` and returns up to `candidate_cap` filtered rows + total (paging done by the use case after ranking). Document this contract in the docstring.
- **Files**: `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` (modify), `tests/test_report_repository.py` (create or modify)
- **References**: `product-design/conventions.md`
- **Depends on**: Step 1
- **Verify**: `uv run pytest tests/test_report_repository.py` passes; `uv run ruff check src/ tests/` clean.
- **Tests**: multi-value `urgencies=[alta,media]` returns both and excludes baixa; `report_type_ids` `IN`; `text="esquina"` matches case-insensitively; `find_page(order="recent", limit=2, offset=0)` returns newest-first page + correct total; `candidate_cap` bounds the returned rows.

### Step 3: Add a semantic ranker over a candidate set (Chroma, ranker-only)
Add a ranking capability to the semantic port without changing the existing `search`/`similar`:
- In `src/fala_gavea/domain/repositories/semantic_ports.py`, add to `ISemanticSearchPort`: `rank(self, query: str, ids: list[str]) -> dict[str, float]` — returns a similarity score in [0,1] for each id that exists in the index (missing ids omitted).
- In `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`, implement `rank`: embed the query once (`_encode_query`), `self._collection.get(ids=ids, include=["embeddings"])`, compute cosine similarity in numpy against the returned embeddings, map distance->score consistent with `search` (`1/(1+dist)` or cosine normalized to [0,1]); return `{id: score}`. No `where` filter, no metadata mirroring — purely scores the SQL-filtered candidate ids.
- **Files**: `src/fala_gavea/domain/repositories/semantic_ports.py` (modify), `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` (modify)
- **References**: `product-design/conventions.md` (Convention 1: semantic calls only through infrastructure)
- **Depends on**: none
- **Verify**: `uv run pyright src/` clean; manual: `rank("buraco", [id1,id2])` returns scores, ranks a buraco report above an unrelated one.
- **Tests**: a fake `ISemanticSearchPort` in the use-case test (Step 4) covers orchestration; a light infra test asserts `rank` returns a score per indexed id and omits unknown ids (skip if Chroma not available in CI, mirroring existing semantic-test gating).

### Step 4: `QueryReports` use case — filter -> rank -> paginate
Create `src/fala_gavea/application/use_cases/reports/query_reports.py`:
- `QueryReports(report_repo, search_port: ISemanticSearchPort | None)`; `execute(filters: ReportFilters, *, q: str | None, limit: int, offset: int, max_results: int) -> QueryPage`.
- Flow: if `q` is truthy **and** `search_port is not None`: fetch filtered candidates via `find_page(filters, limit=max_results, offset=0, order="none", candidate_cap=max_results)`; call `search_port.rank(q, [r.id for r in rows])`; sort rows by score desc (rows missing a score sort last); `total = len(rows)`; slice `[offset:offset+limit]`; `ranked_by="similarity"`, attach per-row score. Else: `rows, total = find_page(filters, limit=limit, offset=offset, order="recent", candidate_cap=max_results)`; `ranked_by="recency"`, score=None.
- Return a `QueryPage` dataclass: `items: list[tuple[Report, float | None]]`, `total: int`, `limit`, `offset`, `ranked_by`.
- **Files**: `src/fala_gavea/application/use_cases/reports/query_reports.py` (create), `tests/test_query_reports.py` (create)
- **References**: `product-design/conventions.md`
- **Depends on**: Step 1, 2, 3
- **Verify**: `uv run pytest tests/test_query_reports.py` passes; `uv run pyright src/` clean.
- **Tests** (fake repo + fake ranker): with `q` set, items are ordered by descending score and `ranked_by="similarity"`; pagination slices the ranked list (`offset`/`limit` correct, `total` = full filtered count); without `q`, order is recency and `ranked_by="recency"`; `search_port=None` falls back to recency even when `q` is set; `max_results` caps the candidate set.

### Step 5: `POST /reports/query` endpoint + schemas
Add the unified endpoint in `src/fala_gavea/presentation/api/routers/reports.py` and schemas in `src/fala_gavea/presentation/schemas/report.py`:
- Request `ReportQueryRequest` (Pydantic): `report_type_ids: list[str] = []`, `urgencies: list[str] = []`, `statuses: list[str] = []`, `since: datetime | None`, `until: datetime | None`, `bbox: str | None`, `text: str | None`, `q: str | None`, `limit: int = 50` (1..200), `offset: int = 0` (>=0). Validate enum membership for urgencies/statuses (reuse the existing `Urgency`/`ReportStatus` enums) -> 422 on bad values; reuse `_parse_bbox`.
- Response `ReportQueryResponse`: `items: list[ReportQueryItem]` (ReportResponse fields + `score: float | None`), `total: int`, `limit: int`, `offset: int`, `ranked_by: str`.
- Route `@router.post("/query", response_model=ReportQueryResponse)`, `current_user = Depends(get_current_user)` (role-scoped like the rest; semantic ranking never widens visibility — same data the user can already list), `report_repo`, `search_port = Depends(get_semantic_search_port)`. Build `ReportFilters` (wrapping the lists), enforce `max_results` (module const, e.g. 500), call `QueryReports(...).execute(...)`, map to the envelope. Register before `GET /{id}` is irrelevant (distinct method+path) but place it near `/search` for readability.
- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify), `src/fala_gavea/presentation/schemas/report.py` (modify), `tests/test_reports_query_api.py` (create)
- **References**: `product-design/conventions.md` (Convention 2: auth via dependencies), `general/review-perspectives/api.md`
- **Depends on**: Step 4
- **Verify**: `uv run pytest tests/test_reports_query_api.py` passes; `uv run ruff check src/ tests/` clean; `uv run pyright src/` clean.
- **Tests**: `POST /reports/query` with `urgencies=["alta","media"]` returns only those; bad enum -> 422; pagination envelope fields correct; `q` present with semantic stub orders by score and sets `ranked_by="similarity"`; unauthenticated -> 401; semantic-unavailable still returns recency results (200, `ranked_by="recency"`).

### Step 6: Adapt the two legacy call sites to the plural `ReportFilters`
Keep `/reports/geojson` and `/reports/keywords` working after Step 1's rename. In `src/fala_gavea/presentation/api/routers/reports.py`, where `ReportFilters(...)` is constructed for `list_reports_geojson` and `get_keywords`, wrap singletons: `report_type_ids=[q.type_id] if q.type_id else None`, `urgencies=[Urgency(q.urgency)] if q.urgency else None`, `statuses=[ReportStatus(q.status)] if q.status else None`. No change to `ReportFiltersQuery` (legacy endpoints stay single-value).
- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- **References**: `product-design/conventions.md`
- **Depends on**: Step 1
- **Verify**: existing geojson/keywords tests still pass (`uv run pytest`); `uv run pyright src/` clean.
- **Tests**: existing `/reports/geojson` + `/reports/keywords` tests remain green (regression guard); add one asserting geojson with `urgency=alta` still filters correctly through the wrapped list.

### Step 7: Frontend — unified query client + hook retarget
Wire research-000129's data layer to Phase B without touching its UI components.
- `frontend/src/lib/api.ts`: add `queryReports(body: ReportQueryBody): Promise<ReportQueryResponse>` POSTing to `/reports/query`. Add `ReportQueryBody`/`ReportQueryResponse`/`ReportQueryItem` to `frontend/src/lib/types.ts` (items carry ReportDetail fields + `score: number | null`; envelope has `total/limit/offset/ranked_by`).
- `frontend/src/hooks/useFilteredReports.ts` + `useSemanticSearch.ts`: build the unified body from the committed `WorkspaceFilters` — map single-value store fields into the lists (`type_id` -> `report_type_ids:[type_id]`, `urgency` -> `urgencies:[urgency]`, `status` -> `statuses:[status]`), pass `bbox`/`since`/`until`/`text`, and `q = semanticQuery`. Call `queryReports`; **adapt the returned `items` into the existing GeoJSON `features` + `count` shape** the views consume, so MapView/TableView/keywords need no change. When `semanticQuery` is set, `ranked_by` is "similarity" and the table/map keep the returned order; expose `count = total`. Keep react-query keying on the body. Default `limit` (e.g. 200) for now — full pagination UI is future (note it).
- **Files**: `frontend/src/lib/api.ts` (modify), `frontend/src/lib/types.ts` (modify), `frontend/src/hooks/useFilteredReports.ts` (modify), `frontend/src/hooks/useSemanticSearch.ts` (modify), `frontend/src/lib/api.test.ts` (modify), `frontend/src/hooks/useFilteredReports.test.ts` (modify if present)
- **References**: `product-design/conventions.md`
- **Depends on**: Step 5
- **Verify**: `cd frontend && npm run test` passes; `npx tsc --noEmit` clean; the workspace still renders map+table filtered results against the new endpoint.
- **Tests** (mock `fetch`): `queryReports` POSTs to `/reports/query` with the lists derived from single-value filters; the hook adapts `items` into features and sets `count=total`; a `semanticQuery` produces a body with `q` and preserves returned order.
- **Docs**: note the endpoint change in API reference (the workspace now queries `POST /reports/query`).

### Step 8: Cross-reference plan-000131 (front-end depends on Phase B)
Add a short dependency note to `_output/plans/plan-000131-refine-data-exploration-search-filters.md` (Agent interpretation or a new "## Dependency" line): record that its FilterPanel/views now read through the unified `POST /reports/query` introduced by plan-000132, that `useFilteredReports`/`useSemanticSearch` retarget happens in plan-000132 Step 7, and that R2's catch-all guard (`/report_types`, `/forwardings`) remains valid and independent. This keeps the two plans coherent for whoever implements them.
- **Files**: `_output/plans/plan-000131-refine-data-exploration-search-filters.md` (modify)
- **References**: none
- **Depends on**: none
- **Verify**: the note is present and references plan-000132 Step 7.
- **Tests**: N/A (documentation cross-reference).

---

## Review Log (standard depth)

The design was evaluated end-to-end by the `research-reviewer` at research-000130 (SEC/ARCH/API/PERF/DB/DATA/UX/AI). Those findings are carried forward; this plan implements only Phase B + the frontend retarget.

| Perspective | Status | Note |
|-------------|--------|------|
| ARCH | Adopted | SQL stays the filter source of truth; Chroma is a ranker via the new `rank()` only — no metadata mirroring, no dual-write. `QueryReports` orchestrates filter->rank->paginate; semantic access stays inside `infrastructure/` (Convention 1). One filter model (`ReportFilters`) avoids duplication; legacy sites adapted (Step 6). |
| API | Adopted | Additive `POST /reports/query` with a JSON body (right shape for multi-value + pagination per research-000130 F4); `/geojson` + `/search` untouched so plan-000131's in-flight SPA is not broken. Stable envelope `{items,total,limit,offset,ranked_by}`. |
| PERF | Adopted | Filter-then-rank-in-memory at this scale (research-000130 F1/F2); `max_results`/`candidate_cap` (500) bounds Railway memory; pagination computed over the fully-ranked set so pages are deterministic. |
| SEC | Adopted | Endpoint role-scoped via `get_current_user`; semantic ranking cannot widen visibility beyond what the user can already list (same query path). Enum/bbox validation -> 422; `text` uses parameterized `ilike` (no SQL injection). |
| TEST | Adopted | Repo, ranker, use case, endpoint, legacy-regression, and frontend client all carry tests; semantic infra test gated like existing semantic tests. |
| DATA / DB | Adopted | No schema migration in Phase B (no new tables — saved filters are Phase C). No PII surface change; `text` filter operates on existing report text already visible to the role. |
| UX | Deferred | Multi-value chips, pagination controls, and the NL draft populate are research-000129 / Phase A concerns; here the frontend retarget is transparent (same map/table/count UX, now backed by the unified endpoint). |
| DX | Adopted | `find_page` contract + `QueryPage`/envelope documented; `rank()` added without disturbing `search`/`similar`. |
| I18N / VIS / RESP / OPS / COMPAT | N/A | No locale/visual-token/breakpoint/deploy/external-contract changes; legacy endpoints preserved (COMPAT safe). |

**Deferred / out of scope**: Phase A NL-to-filter assistant (Ollama `format` + Pydantic + editable draft); Phase C per-user saved filters (`saved_filters` table, owner-scoped CRUD); multi-value filter UI and pagination controls in the FilterPanel (research-000129 follow-up); retiring `/geojson` + `/search` (after the SPA fully migrates).

## Test plan (manual)

1. Auth as agent. `POST /reports/query` `{ "urgencies": ["alta","media"], "limit": 10 }` -> only alta/media reports, `ranked_by:"recency"`, newest first, `total` reflects the full filtered count.
2. `POST /reports/query` `{ "q": "buraco na calçada", "limit": 5 }` -> results ordered by similarity, each `item.score` populated, `ranked_by:"similarity"`.
3. Combine: `{ "statuses":["pendente"], "since":"2026-06-01T00:00:00Z", "q":"iluminação" }` -> filtered to pendente since the date, ranked by similarity.
4. Pagination: same query with `offset:5,limit:5` returns the next page; `total` unchanged across pages.
5. Bad enum `{ "urgencies":["altissima"] }` -> 422.
6. Frontend: open the workspace; existing Tipo/Urgencia/Status/date/bbox filters still produce the map+table results (now via `/reports/query`); a semantic query reorders by relevance; counts match.
7. Regression: `/reports/geojson` and the keywords view still work.

## Manual actions after implementation

- Backend only: `uv run pytest` then restart the API (`uv run uvicorn fala_gavea.presentation.api.main:app`).
- Frontend: `cd frontend && npm run build` (or `npm run dev` against the API) so the workspace exercises the new endpoint.
- No DB migration in Phase B. (Phase C saved filters will add one.)

---

## Implementation Summary

**Completed**: 2026-06-21 18:39 UTC | 8/8 steps | 7 iterations (Steps 1+3+8 parallel, then 2+4 parallel, then 5, then 7)

### Steps completed
- [x] Step 1: Extended `ReportFilters` to multi-value (`report_type_ids`, `urgencies`, `statuses`) + `text`; added `find_page` abstract method; updated SQLAlchemy `find_all` to `.in_()`/`.ilike()` and implemented `find_page` with count subquery + offset/limit.
- [x] Step 2: Tests for SQLAlchemy repo — 7 tests covering multi-value IN, ilike, find_page ordering/pagination/candidate_cap. All pass.
- [x] Step 3: Added `rank(query, ids) -> dict[str, float]` to `ISemanticSearchPort` and implemented in `ChromaSearchClient` using cosine similarity.
- [x] Step 4: Created `QueryReports` use case with `QueryPage` dataclass; two-path logic (semantic rank-in-memory vs recency SQL). 5 tests with fake in-memory implementations.
- [x] Step 5: `POST /reports/query` endpoint with `ReportQueryRequest`/`ReportQueryItem`/`ReportQueryResponse` schemas; 6 API tests all green.
- [x] Step 6: Legacy call sites (`/reports/geojson`, `/reports/keywords`) already updated in Step 1 to wrap singletons in lists.
- [x] Step 7: Frontend retarget — added `queryReports()` to `api.ts`, new types to `types.ts`, rewrote `useFilteredReports` as single unified `useQuery`; 33/33 frontend tests pass.
- [x] Step 8: Cross-reference note added to plan-000131.

### Quality Gate
- pytest: 136 passed
- ruff: 7 unused import warnings (auto-fixed)
- Frontend tests: 33 passed, tsc clean

### Generator-Critic Iterations
- Iteration count: 0/2
- Findings per iteration: []
- Resolution status: all resolved
