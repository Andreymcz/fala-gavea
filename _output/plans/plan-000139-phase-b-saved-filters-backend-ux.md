# DONE | 2026-06-21 23:05 UTC | Plan 000139 | feat/saved-filters | 2026-06-21 22:40 UTC | Phase B: saved filters backend + UX | Review: standard
plan_format_version: 1

## Context

Phase B of the left-panel search engine redesign (research-000136). Phase A (plan-000137) delivered the four-section FilterPanel, draft/Apply model, `loadedPresetName`/`draftFilterName` in the store, and the preset bar as *placeholders*. Phase B activates those placeholders by wiring real saved-filter CRUD.

**What Phase A already delivered (do NOT re-implement):**
- `workspaceStore.ts` — `loadedPresetName`, `draftFilterName`, `setLoadedPresetName`, `setDraftFilterName`, `panelOpen`, `draftFilters`, `applyFilters`, `isDirty()`.
- `FilterPanel.tsx` — four-section layout including a Section 1 preset bar scaffold with disabled/placeholder Save and Load controls.
- Draft-loss guard via `useBlocker`.

**What this plan adds:**
1. **Backend:** `SavedFilter` domain entity + `ISavedFilterRepository` port → `SavedFilterModel` (SQLAlchemy, auto-created via `create_tables()`) → `SQLAlchemySavedFilterRepository` → 5 use cases → Pydantic schemas → `GET/POST/PATCH/DELETE /saved-filters` router.
2. **Frontend:** API client functions + types → activate the Section 1 preset bar (Save popover with name input, Load dropdown with per-item delete, `*` dirty indicator).

**No Alembic migration needed:** the project uses `Base.metadata.create_all()` in `create_tables()` (called on every startup). Adding `SavedFilterModel` to `models.py` is sufficient.

**Security invariant (F5/R9 from research-000136):** every SQL query on `saved_filters` includes `WHERE owner_id = current_user.id`. Non-owned resources return **404** (not 403) to prevent BOLA disclosure.

---

## Source

- research-000136 §F4 (saved filter UX flow), §F5 (backend schema + endpoints), §R4, §R6, §R9
- plan-000137 (Phase A — FilterPanel four-section layout already implemented)
- As-coded: `src/fala_gavea/presentation/api/main.py`, `dependencies.py`, `infrastructure/database/models.py`, `presentation/api/routers/forwardings.py` (router pattern)
- Frontend: `frontend/src/store/workspaceStore.ts`, `frontend/src/features/workspace/FilterPanel.tsx`

---

## Steps

### Step 1: Domain layer — `SavedFilter` entity + `ISavedFilterRepository` port

Create the pure domain objects with no infrastructure dependencies.

**`SavedFilter` dataclass** (`domain/entities/saved_filter.py`):
```python
@dataclass
class SavedFilter:
    id: str          # UUID4
    owner_id: str    # FK → users.id
    name: str        # 1–80 chars
    body: str        # JSON string: ReportQueryBody subset
    schema_ver: str  # defaults to "1"
    created_at: datetime
    updated_at: datetime
```

**`ISavedFilterRepository`** (`domain/repositories/saved_filter_repository.py`):
```python
class ISavedFilterRepository(ABC):
    def save(self, sf: SavedFilter) -> SavedFilter: ...
    def find_by_id(self, id: str) -> SavedFilter | None: ...
    def find_all_for_user(self, owner_id: str) -> list[SavedFilter]: ...
    def update(self, sf: SavedFilter) -> SavedFilter: ...
    def delete(self, id: str) -> None: ...
```

- **Files**: `src/fala_gavea/domain/entities/saved_filter.py` (create), `src/fala_gavea/domain/repositories/saved_filter_repository.py` (create)
- **References**: N/A
- **Interface**: exports `SavedFilter` dataclass; exports `ISavedFilterRepository` ABC with the 5 methods listed above
- **Verify**: `uv run python -c "from fala_gavea.domain.entities.saved_filter import SavedFilter; from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository; print('ok')"` exits 0
- **Tests**: Add unit tests in `tests/domain/test_saved_filter.py` — verify `SavedFilter` dataclass fields are correctly typed; verify `ISavedFilterRepository` is abstract (cannot be instantiated)
- [x] Done

---

### Step 2: Infrastructure — `SavedFilterModel` + `SQLAlchemySavedFilterRepository`

Add the SQLAlchemy model and its repository implementation.

**`SavedFilterModel`** — add to `infrastructure/database/models.py`:
```python
class SavedFilterModel(Base):
    __tablename__ = "saved_filters"
    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    body = Column(String, nullable=False)        # JSON string
    schema_ver = Column(String, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
```
No index needed in SQLAlchemy column definition for SQLite; `find_all_for_user` queries by `owner_id` which SQLite handles without explicit index at PoC scale.

**`SQLAlchemySavedFilterRepository`** — `infrastructure/repositories/sqlalchemy_saved_filter_repository.py`:
- `save`: insert `SavedFilterModel`, return mapped `SavedFilter`
- `find_by_id`: `SELECT WHERE id = ?` — return `SavedFilter | None` (do NOT filter by owner here; ownership check is in the use cases)
- `find_all_for_user`: `SELECT WHERE owner_id = ?` ORDER BY `created_at DESC`
- `update`: load model by id, patch `name`/`body`/`schema_ver`/`updated_at`, return mapped `SavedFilter`
- `delete`: `DELETE WHERE id = ?`

Mapper helper `_to_entity(m: SavedFilterModel) -> SavedFilter` — private function within the module.

- **Files**: `src/fala_gavea/infrastructure/database/models.py` (modify), `src/fala_gavea/infrastructure/repositories/sqlalchemy_saved_filter_repository.py` (create)
- **Depends on**: Step 1
- **Interface**: exports `SQLAlchemySavedFilterRepository(db: Session)` implementing `ISavedFilterRepository`
- **Verify**: `uv run pytest tests/infrastructure/test_sqlalchemy_saved_filter_repository.py -x` passes; `create_tables()` creates `saved_filters` table (verified by running `uv run python -c "from fala_gavea.infrastructure.database.session import create_tables; create_tables(); print('ok')"`)
- **Tests**: Add `tests/infrastructure/test_sqlalchemy_saved_filter_repository.py` — in-memory SQLite session, test all 5 methods: save returns entity; find_by_id returns None for missing; find_all_for_user returns only own entries; update changes name+body; delete removes entry
- [x] Done

---

### Step 3: Application layer — 5 use cases

Create `application/use_cases/saved_filters/` package with one file per use case. All use cases receive `ISavedFilterRepository` and the calling `User` (or their `user_id`) as constructor/execute arguments — **never derive ownership from request body**.

**`CreateSavedFilter`** (`create_saved_filter.py`):
- Validates `name` (1–80 chars, trimmed); raises `InvalidInputError` on violation
- Generates `id = str(uuid.uuid4())`, `created_at = updated_at = datetime.utcnow()`
- Calls `repo.save(SavedFilter(...))`; returns `SavedFilter`

**`ListSavedFilters`** (`list_saved_filters.py`):
- Calls `repo.find_all_for_user(owner_id)`; returns `list[SavedFilter]` (already ordered by `created_at DESC` from repo)

**`GetSavedFilter`** (`get_saved_filter.py`):
- Calls `repo.find_by_id(id)`; if None **or** `sf.owner_id != owner_id` → raise `NotFoundError` (404, never 403 — BOLA prevention)

**`UpdateSavedFilter`** (`update_saved_filter.py`):
- `GetSavedFilter` ownership check first (reuse or inline)
- Patches `name` (if provided) and `body` (if provided); sets `updated_at = datetime.utcnow()`; calls `repo.update(sf)` ; returns `SavedFilter`

**`DeleteSavedFilter`** (`delete_saved_filter.py`):
- Ownership check (same pattern as Get); calls `repo.delete(id)`; returns `None`

Add `domain/exceptions.py` `NotFoundError` if not already present. Check first — if a `NotFoundError` exists (or `ResourceNotFoundError`), reuse it.

- **Files**: `src/fala_gavea/application/use_cases/saved_filters/__init__.py` (create, empty), `src/fala_gavea/application/use_cases/saved_filters/create_saved_filter.py` (create), `src/fala_gavea/application/use_cases/saved_filters/list_saved_filters.py` (create), `src/fala_gavea/application/use_cases/saved_filters/get_saved_filter.py` (create), `src/fala_gavea/application/use_cases/saved_filters/update_saved_filter.py` (create), `src/fala_gavea/application/use_cases/saved_filters/delete_saved_filter.py` (create), `src/fala_gavea/domain/exceptions.py` (modify if `NotFoundError` missing)
- **Depends on**: Step 1
- **Interface**: each use case class has an `.execute(...)` method; `CreateSavedFilter(repo).execute(owner_id, name, body) -> SavedFilter`; `GetSavedFilter(repo).execute(id, owner_id) -> SavedFilter`; `DeleteSavedFilter(repo).execute(id, owner_id) -> None`
- **Verify**: `uv run pytest tests/application/test_saved_filter_use_cases.py -x` passes
- **Tests**: Add `tests/application/test_saved_filter_use_cases.py` using an in-memory `SQLAlchemySavedFilterRepository` (or a simple stub). Test: create → get returns it; get with wrong owner_id raises NotFoundError; update patches fields; delete removes; list returns only own entries; create with name > 80 chars raises InvalidInputError
- [x] Done

---

### Step 4: Presentation layer — schemas + router + wire into main

**Schemas** (`presentation/schemas/saved_filter.py`):
```python
class SavedFilterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    body: dict[str, Any]   # validated against ReportQueryBody subset on read; stored as JSON string

class SavedFilterUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    body: dict[str, Any] | None = None

class SavedFilterResponse(BaseModel):
    id: str
    name: str
    body: dict[str, Any]
    schema_ver: str
    created_at: datetime
    updated_at: datetime
    deprecated_fields: list[str] = []  # fields dropped on load (graceful schema migration)
```

**Router** (`presentation/api/routers/saved_filters.py`):
```
POST   /saved-filters          → 201 SavedFilterResponse  (create)
GET    /saved-filters          → 200 list[SavedFilterResponse]  (list own)
GET    /saved-filters/{id}     → 200 | 404  (read own)
PATCH  /saved-filters/{id}     → 200 SavedFilterResponse  (update own)
DELETE /saved-filters/{id}     → 204  (delete own)
```

All require `get_current_user`. Router delegates to use cases.

`body` is stored as `json.dumps(body)` and returned as `json.loads(sf.body)`. On GET/PATCH, validate the deserialized body against `ReportQueryBody` Pydantic model; collect dropped fields into `deprecated_fields` list (any key in the stored dict not in `ReportQueryBody.__fields__`).

**`dependencies.py`**: add:
```python
def get_saved_filter_repo(db: Session = Depends(get_db)) -> ISavedFilterRepository:
    from fala_gavea.infrastructure.repositories.sqlalchemy_saved_filter_repository import SQLAlchemySavedFilterRepository
    return SQLAlchemySavedFilterRepository(db)
```

**`main.py`**: 
- Import and include `saved_filters_router` at prefix `/saved-filters`
- Add `"saved-filters"` to `_API_PREFIXES` set

- **Files**: `src/fala_gavea/presentation/schemas/saved_filter.py` (create), `src/fala_gavea/presentation/api/routers/saved_filters.py` (create), `src/fala_gavea/presentation/api/dependencies.py` (modify), `src/fala_gavea/presentation/api/main.py` (modify)
- **Depends on**: Step 2, Step 3
- **Interface**: exposes `router = APIRouter()` at `saved_filters.py`; `SavedFilterResponse` Pydantic model
- **Verify**: `uv run pytest tests/presentation/test_saved_filters_router.py -x` passes; `uv run uvicorn fala_gavea.presentation.api.main:app` starts without error
- **Tests**: Add `tests/presentation/test_saved_filters_router.py` — use FastAPI `TestClient`; test: unauthenticated → 401; create → 201 with id+name+body; list → returns created; get → 200; get with another user's id → 404; patch → 200 with new name; delete → 204; get after delete → 404
- **Docs**: Update API reference contextual help if present (search `_output/` for existing docs)
- [x] Done

---

### Step 5: Frontend — API client functions + types

Add TypeScript types and API functions for the 5 saved-filter endpoints.

**Types** (`frontend/src/lib/types.ts` — add):
```typescript
export interface SavedFilter {
  id: string
  name: string
  body: Partial<ReportFilters & { q?: string }>
  schema_ver: string
  created_at: string
  updated_at: string
  deprecated_fields: string[]
}

export interface SavedFilterCreate {
  name: string
  body: Partial<ReportFilters & { q?: string }>
}

export interface SavedFilterUpdate {
  name?: string
  body?: Partial<ReportFilters & { q?: string }>
}
```

**API functions** (`frontend/src/lib/api.ts` — add):
```typescript
createSavedFilter(data: SavedFilterCreate): Promise<SavedFilter>
listSavedFilters(): Promise<SavedFilter[]>
getSavedFilter(id: string): Promise<SavedFilter>
updateSavedFilter(id: string, data: SavedFilterUpdate): Promise<SavedFilter>
deleteSavedFilter(id: string): Promise<void>
```

All functions call `/saved-filters` with `Authorization: Bearer <token>` (same auth pattern as existing `api.ts` functions).

- **Files**: `frontend/src/lib/types.ts` (modify), `frontend/src/lib/api.ts` (modify)
- **Depends on**: Step 4
- **Interface**: exports `createSavedFilter`, `listSavedFilters`, `getSavedFilter`, `updateSavedFilter`, `deleteSavedFilter` from `api.ts`; exports `SavedFilter`, `SavedFilterCreate`, `SavedFilterUpdate` from `types.ts`
- **Verify**: `cd frontend && npm run build` succeeds (type check passes)
- **Tests**: Add or extend `frontend/src/lib/api.test.ts` — mock fetch; verify each function sends the correct method/path/body; verify `deleteSavedFilter` resolves `void` on 204
- [x] Done

---

### Step 6: Frontend UX — activate Section 1 preset bar in `FilterPanel`

Activate the placeholder Save/Load controls in Section 1 of `FilterPanel.tsx` using `react-query` mutations + queries against the API functions from Step 5.

**Behavior spec (from research-000136 F4, R6):**

**Load dropdown** (`Carregar` button or Select trigger):
- On open: calls `listSavedFilters()` (react-query, `staleTime: 30s`).
- Each item shows its `name`; clicking loads: `getSavedFilter(id)` → `setDraftFilter(body)` → `setLoadedPresetName(name)` in store.
- Each item has a trash icon button; clicking calls `deleteSavedFilter(id)` (mutation) then invalidates the list query. Confirmation: tooltip-level — a `title` attribute ("Remover filtro") suffices; no full dialog.

**Save popover:**
- `Salvar` button opens a small inline popover (Radix `Popover` or `Dialog`) with a `<input>` for filter name (pre-filled with `draftFilterName` from store, or auto-name from chip summary if empty).
- Auto-name: join active draft filter labels, e.g. `"Alta, Vandalismo, últimos 30 dias"` truncated to 40 chars.
- "Confirmar" button: calls `createSavedFilter({ name, body: filters })` (current **committed** filters, not draft — save what is active). On success: `setLoadedPresetName(name)` in store; invalidate list query.
- If a preset is already loaded (`loadedPresetName !== null`): offer a secondary "Atualizar" option that calls `updateSavedFilter(id, { body: filters })` to overwrite the current preset.

**Header name display:**
- Show `loadedPresetName ?? "Sem filtro salvo"` in Section 1 text.
- When `loadedPresetName !== null && isDirty()`: append `*` to the name to signal the loaded preset has been modified since loading.

**Store updates** — `workspaceStore.ts`:
- Add `loadedPresetId: string | null` (to track which preset id is loaded, needed for the "Atualizar" flow). Add corresponding `setLoadedPresetId`.
- Modify `setLoadedPresetName` calls to also clear `loadedPresetId` when `null`.
- In `clearFilters()`: also reset `loadedPresetId: null`.

**Graceful degradation:** if `listSavedFilters()` returns an error, show "Erro ao carregar filtros salvos" in the dropdown; individual items remain functional.

- **Files**: `frontend/src/features/workspace/FilterPanel.tsx` (modify), `frontend/src/store/workspaceStore.ts` (modify — add `loadedPresetId`)
- **Depends on**: Step 5
- **Verify**: `cd frontend && npm run build` passes; `cd frontend && npm run test` passes
- **Tests**: Add tests in `frontend/src/features/workspace/FilterPanel.test.tsx` — mock API; verify Save popover appears on "Salvar" click; verify auto-name generation when `draftFilterName` is empty; verify Load dropdown shows fetched names; verify trash icon calls `deleteSavedFilter`; verify `*` appears when loaded preset is dirty
- [x] Done

---

## Review

**Complexity gate:** standard (2 architectural layers — backend + frontend; 1 new entity; 5 use cases; CRUD router; UX interaction)

**Security (P0):**
- BOLA prevention enforced: every `find_by_id` result is ownership-checked in the use case before returning; non-owned → 404 not 403 (per OWASP BOLA guidance in research-000136 R9). Adopted.
- `owner_id` is always taken from `current_user.id` (JWT), never from the request body. Adopted.
- `body` is stored as a plain JSON string; deserialized server-side through Pydantic before serving to the client — no eval or arbitrary code path. Adopted.

**Correctness (P1):**
- `find_by_id` in repo does NOT filter by owner; ownership check is a use-case responsibility. This makes the repo testable in isolation and avoids a subtle bug where a future admin list endpoint could silently exclude items. Adopted.
- `create_tables()` auto-creates `saved_filters` on startup; no migration script needed given existing pattern. Adopted.
- `deprecated_fields` list on response allows stale saved filters to degrade gracefully without 422. Adopted.

**Testability (P3):**
- Each layer (domain → infra → use case → router → frontend) has isolated unit tests. Adopted.
- Router tests use `TestClient` with a real in-memory SQLite database to avoid mock/prod divergence. Adopted.

**Performance (deferred):** no index on `owner_id` in SQLAlchemy model column definition — `find_all_for_user` does a full-table scan. At PoC scale (<10k rows, single user per session) this is acceptable. Deferred.

---

## Commit message

```
feat(saved-filters): Phase B — backend CRUD + preset bar UX

SavedFilter entity + ISavedFilterRepository port; SavedFilterModel
(auto-created via create_tables); SQLAlchemySavedFilterRepository;
5 use cases (Create/List/Get/Update/Delete); SavedFilterResponse
schemas; CRUD router at /saved-filters; dependency + main.py wiring.
Frontend: SavedFilter types + 5 api.ts functions; FilterPanel Section 1
activated with Save popover (name input, auto-name fallback, Atualizar
for loaded presets), Load dropdown (name list + trash icon), * dirty
indicator when loaded preset is modified. BOLA: owner_id always from
JWT, non-owned resources → 404.
```

---

## Implementation Summary

**Completed:** 6/6 steps | **Iterations:** 6 | **Partial/Failed:** 0

### Steps Completed
1. Domain layer: `SavedFilter` dataclass + `ISavedFilterRepository` ABC
2. Infrastructure: `SavedFilterModel` (SQLAlchemy, auto-created via `create_tables()`) + `SQLAlchemySavedFilterRepository` with all 5 methods
3. Application: 5 use cases (Create/List/Get/Update/Delete) with BOLA ownership enforcement via 404 for non-owned resources
4. Presentation: Pydantic schemas, CRUD router at `/saved-filters`, dependency + `main.py` wiring
5. Frontend: `SavedFilter` types + 5 `api.ts` functions (create/list/get/update/delete)
6. Frontend UX: `FilterPanel` Section 1 preset bar — Save popover (name input, auto-name, Atualizar), Load dropdown (names + trash), `*` dirty indicator; `workspaceStore` extended with `loadedPresetId`

### Quality Gate
- ruff: all checks passed (after fixing F821 return type annotation + F401 unused import)
- pytest backend: 129/130 passed (1 pre-existing failure in `test_static_spa.py`, unrelated to this plan)
- npm test: 94/94 passed

### Post-Review Fixes Applied
- `get_saved_filter_repo`: added `-> "ISavedFilterRepository"` return type via `TYPE_CHECKING` guard
- `SavedFilterModel`: `DateTime(timezone=True)` to prevent silent tz stripping on SQLite round-trips
- `_to_response`: wrapped `json.loads` in `try/except JSONDecodeError` to avoid 500 on malformed stored body
- `UpdateSavedFilter.execute`: early return if both `name` and `body` are `None` (no-op PATCH guard)

### Deferred Findings (non-blocking)
- Body size cap (MEDIUM): no `max_length` check on `body` JSON; acceptable at PoC scale
- A11Y: emoji trash icon (`🗑`) could use SVG; `aria-expanded` missing on popover triggers
- No Alembic migration (by plan design; `create_tables()` auto-creates on startup)
