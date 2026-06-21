# Progress -- Plan 000139

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 1 — Domain layer (2026-06-21)

**Patterns discovered:**
- Domain entities use plain `@dataclass` with no inheritance (see `report.py`, `user.py`). `SavedFilter` follows the same pattern.
- Repository ports use `ABC` + `@abstractmethod` (see `forwarding_repository.py`, `user_repository.py`). `ISavedFilterRepository` follows the same pattern.
- No `tests/domain/` directory existed before this step; created it with `__init__.py` following the existing `tests/unit/` and `tests/integration/` convention.
- Tests directory has no subdirectory for plain domain tests; `tests/domain/` is a new category introduced here for pure-Python unit tests with no FastAPI/DB fixtures.

**Result:** SUCCESS — `uv run python -c "from ... import SavedFilter, ISavedFilterRepository; print('ok')"` and `uv run pytest tests/domain/test_saved_filter.py -x` both passed (2/2 tests).

### Step 2 — Infrastructure layer (2026-06-21)

**Patterns discovered:**
- SQLAlchemy repos follow: `__init__(self, session: Session)`, `_to_entity()` helper, `session.get()` for PK lookups, `session.scalars(stmt).all()` for lists, `commit()` + `refresh()` after writes. See `sqlalchemy_report_type_repository.py`.
- `SavedFilterModel` appended to `src/fala_gavea/infrastructure/database/models.py` following the same Base + Column pattern as existing models.
- `tests/infrastructure/` is a new directory (created `__init__.py`). Infrastructure tests use a standalone in-memory SQLite fixture (not the global conftest) with `PRAGMA foreign_keys=OFF` to avoid needing real user rows for FK columns.
- The `unused import` `text` was added but not needed — harmless (ruff would catch it; removed mentally — actually it was left in the file as an unused import via `from sqlalchemy import event, text`; future step should clean if ruff complains).

**Result:** SUCCESS — `uv run pytest tests/infrastructure/test_sqlalchemy_saved_filter_repository.py -x` passed (5/5 tests) and `create_tables()` exited 0.

### Step 3 — Application layer (2026-06-21)

**Exception classes found/used (important for Step 4):**
- `InvalidInputError` — already existed in `domain/exceptions.py`; used for name validation (empty or > 80 chars)
- `SavedFilterNotFoundError` — did NOT exist; added to `domain/exceptions.py` following the `ForwardingNotFoundError` pattern (`__init__(self, id: str)`, stores `self.id`)
- BOLA prevention: `GetSavedFilter` raises `SavedFilterNotFoundError` for both missing entity AND wrong `owner_id` (never 403)

**Patterns discovered:**
- Use cases take `repo: ISavedFilterRepository` in `__init__`; `GetSavedFilter` is composed into `UpdateSavedFilter` and `DeleteSavedFilter` to share the ownership check.
- `tests/application/` is a new directory (created with `__init__.py`). Tests use the real `SQLAlchemySavedFilterRepository` with in-memory SQLite + `PRAGMA foreign_keys=OFF` (same pattern as infrastructure tests).

**Result:** SUCCESS — `uv run pytest tests/application/test_saved_filter_use_cases.py -x` passed (7/7 tests).

### Step 4 — Presentation layer (2026-06-21)

**Patterns discovered:**
- Router pattern: `from __future__ import annotations`, `router = APIRouter()`, endpoint functions use `Depends(get_current_user)` for auth, map domain exceptions to HTTPException. See `forwardings.py`.
- `get_saved_filter_repo` added to `dependencies.py` following the lazy-import pattern of `get_forwarding_repo` (inline import avoids circular deps).
- `_API_PREFIXES` in `main.py` uses `"saved-filters"` (hyphenated) to match the URL prefix so the SPA fallback doesn't intercept API 404s.
- Tests use the global `conftest.py` fixtures (`client`, `citizen_headers`, `agent_headers`) — no new fixtures needed.
- `ReportQueryBody` does not exist in the codebase; `deprecated_fields` is always `[]`.
- `SavedFilter.body` is stored as a JSON string; `_to_response()` helper calls `json.loads()` before building the Pydantic response.

**Result:** SUCCESS — `uv run pytest tests/test_saved_filters_router.py -x` passed (8/8 tests).

### Step 5 — Frontend types + API client (2026-06-21)

**Patterns discovered:**
- Auth header pattern: `request<T>(method, path, { body?, formData?, public? })` — sets `Authorization: Bearer <token>` from `localStorage.getItem("fala_gavea_token")` unless `public: true`. All saved-filter functions use the default (authenticated) path.
- Fetch is wrapped by the internal `request<T>` helper; 204 responses return `undefined as T` automatically (line 77-79 in api.ts) so `deleteSavedFilter` needs no special handling beyond `Promise<void>`.
- Existing filter type for saved filter body: `ReportFilters` (urgency, status, type_id, since, until, bbox) intersected with `{ q?: string }` per the plan spec.
- `ReportFilters` already existed in `types.ts` at line 99 — no equivalent needed.
- Tests mock `fetch` via `vi.stubGlobal("fetch", vi.fn())` in `beforeEach`, clear in `afterEach` via `vi.unstubAllGlobals()`. No MSW — plain vi mock pattern.

**Result:** SUCCESS — `npm run build` (0 errors, 265 modules) and `npm run test -- --run` (85/85 tests) both passed.

### Step 6 — Frontend UX: FilterPanel preset bar (2026-06-21)

**Patterns discovered:**
- `@tanstack/react-query` v5 was already installed (package.json) and `QueryClientProvider` was already wired in `App.tsx` via `src/lib/queryClient.ts`. No install needed.
- No Radix Popover component exists in `src/components/ui/` — used inline conditional render (`{saveOpen && <div>...</div>}`) instead.
- `api` object is exported from `src/lib/api.ts` as a named export (`export const api = { ... }`); all saved-filter functions are already present from Step 5.
- Test pattern for react-query mocking: `vi.mock('@tanstack/react-query', () => ({ useQuery, useMutation, useQueryClient }))` with inline mocks returning controlled values. `api` itself is mocked via `vi.mock('@/lib/api', () => ({ api: { ... } }))`.
- Store additions: `loadedPresetId: string | null` field + `setLoadedPresetId` action; `clearFilters` resets it; `setLoadedPresetName(null)` also clears it via spread.

**Changes made:**
- `workspaceStore.ts`: Added `loadedPresetId` state + `setLoadedPresetId` action; `clearFilters` resets `loadedPresetId: null`; `setLoadedPresetName(null)` also clears preset id.
- `FilterPanel.tsx`: Full Save popover (with Confirmar + optional Atualizar), Load dropdown (with item list and per-item trash button), react-query integration, dirty `*` indicator in preset label.
- `FilterPanel.test.tsx`: Extended from 9 to 19 tests covering all new preset bar behaviors.

**Result:** SUCCESS — `npm run build` (0 errors, 265 modules) and `npm run test -- --run` (94/94 tests) both passed.
