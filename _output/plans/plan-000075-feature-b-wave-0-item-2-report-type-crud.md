# Plan 000075 | FEATURE-B fala-gavea | 2026-06-17 21:39 UTC | wave-0-item-2-report-type-crud | Review: light
plan_format_version: 1

source: roadmap-000071 -- Wave 0, Item 2: ReportType CRUD (admin endpoints + public GET + seed script)

## Brief (verbatim)

roadmap 1 item 2

## Agent Interpretation

Implement Wave 0, Item 2 from roadmap-000071: the ReportType CRUD API.

The domain entity (`ReportType`), SQLAlchemy model (`ReportTypeModel`), repository interface
(`IReportTypeRepository`), SQLAlchemy implementation (`SQLAlchemyReportTypeRepository`), and
domain exception (`ReportTypeNotFoundError`) were all created in plan-000073. This plan adds
the missing application layer (use cases), presentation layer (Pydantic schemas + FastAPI router),
and operational tooling (seed script + tests).

Endpoints to implement:
- `GET /report_types` -- public (no auth); returns only active types
- `POST /report_types` -- admin only; creates a new type
- `PATCH /report_types/{id}` -- admin only; updates name and/or description
- `DELETE /report_types/{id}` -- admin only; soft-delete (sets active=False)

Seed script: creates 8 initial types via the HTTP API (exercises POST /report_types).

## Scope

Wave 0, Item 2 from roadmap-000071. Excludes:
- Forwarding endpoints (Item 3, Wave 1)
- Frontend static pages (Item 4, Wave 1)
- ChromaDB / semantic search (Items 5-7, Wave 2)

## Files

### New files
- `src/fala_gavea/application/use_cases/report_types/__init__.py`
- `src/fala_gavea/application/use_cases/report_types/create_report_type.py`
- `src/fala_gavea/application/use_cases/report_types/update_report_type.py`
- `src/fala_gavea/application/use_cases/report_types/delete_report_type.py`
- `src/fala_gavea/presentation/schemas/report_type.py`
- `src/fala_gavea/presentation/api/routers/report_types.py`
- `scripts/seed_report_types.py`
- `tests/test_report_types.py`

### Modified files
- `src/fala_gavea/presentation/api/main.py` (include report_types router)
- `tests/conftest.py` (add admin_headers fixture)

---

## Steps

### Step 1: Pydantic schemas for ReportType

Create `presentation/schemas/report_type.py` with three schemas:

- `ReportTypeCreate(name: str, description: str | None = None)` -- validates name is 3-100 chars
  (trimmed) per design-intent §10.
- `ReportTypeUpdate(name: str | None = None, description: str | None = None)` -- partial update;
  both fields optional (a PATCH with neither field is a no-op but allowed).
- `ReportTypeResponse(id: str, name: str, description: str | None, active: bool, created_at: datetime)`
  with `model_config = {"from_attributes": True}`.

Validation in `ReportTypeCreate`:
```python
@field_validator("name")
@classmethod
def name_length(cls, v: str) -> str:
    v = v.strip()
    if not (3 <= len(v) <= 100):
        raise ValueError("name must be 3-100 characters")
    return v
```

- **Files**: `src/fala_gavea/presentation/schemas/report_type.py` (create)
- **References**: `product-design/project/product-design-as-intended.md §10`, `product-design/project/standards.md § Backend §8`
- **Interface**: Exports `ReportTypeCreate`, `ReportTypeUpdate`, `ReportTypeResponse`
- **Verify**: `uv run python -c "from fala_gavea.presentation.schemas.report_type import ReportTypeCreate, ReportTypeUpdate, ReportTypeResponse"` succeeds
- **Tests**: Covered by Step 5 (integration tests exercise schemas via HTTP)
- [ ] Done

---

### Step 2: Use cases -- CreateReportType, UpdateReportType, DeleteReportType

Create `application/use_cases/report_types/` sub-package with three use cases.
No SQLAlchemy imports -- only domain types and interfaces.

**`create_report_type.py`**:
```python
class CreateReportType:
    def __init__(self, repo: IReportTypeRepository) -> None: ...
    def execute(self, name: str, description: str | None) -> ReportType:
        # strip name; validate 3-100 chars; raise InvalidInputError if fails
        # create ReportType(id=uuid4(), name=name, description=description,
        #   active=True, created_at=datetime.now(UTC))
        # return repo.save(rt)
```

**`update_report_type.py`**:
```python
class UpdateReportType:
    def __init__(self, repo: IReportTypeRepository) -> None: ...
    def execute(self, id: str, name: str | None, description: str | None) -> ReportType:
        # find_by_id; raise ReportTypeNotFoundError if None
        # if name is not None: strip, validate 3-100, set rt.name
        # if description is not None: set rt.description
        # return repo.save(rt)
```

**`delete_report_type.py`**:
```python
class DeleteReportType:
    def __init__(self, repo: IReportTypeRepository) -> None: ...
    def execute(self, id: str) -> None:
        # find_by_id; raise ReportTypeNotFoundError if None
        # set rt.active = False; repo.save(rt)
```

Create `__init__.py` (empty).

- **Files**: `src/fala_gavea/application/use_cases/report_types/__init__.py` (create), `src/fala_gavea/application/use_cases/report_types/create_report_type.py` (create), `src/fala_gavea/application/use_cases/report_types/update_report_type.py` (create), `src/fala_gavea/application/use_cases/report_types/delete_report_type.py` (create)
- **References**: `product-design/project/standards.md § Backend §4`, `product-design/project/product-design-as-intended.md §10`
- **Depends on**: Step 1
- **Interface**: Exports `CreateReportType`, `UpdateReportType`, `DeleteReportType` (each with `.execute()` method)
- **Verify**: `uv run python -c "from fala_gavea.application.use_cases.report_types.create_report_type import CreateReportType"` succeeds
- **Tests**: Covered by Step 5 (integration tests exercise use cases via HTTP)
- [ ] Done

---

### Step 3: Router + main.py registration

Create `presentation/api/routers/report_types.py` with four endpoints:

```
GET  /report_types         -- public (no auth required)
POST /report_types         -- require_role("admin")
PATCH /report_types/{id}   -- require_role("admin")
DELETE /report_types/{id}  -- require_role("admin"), returns 204 No Content
```

Router detail:

```python
router = APIRouter()

@router.get("/", response_model=list[ReportTypeResponse])
def list_report_types(report_type_repo=Depends(get_report_type_repo)):
    # returns repo.find_all_active() mapped to ReportTypeResponse

@router.post("/", response_model=ReportTypeResponse, status_code=201)
def create_report_type(
    body: ReportTypeCreate,
    current_user: User = Depends(require_role("admin")),
    report_type_repo=Depends(get_report_type_repo),
):
    try:
        rt = CreateReportType(report_type_repo).execute(body.name, body.description)
        return ReportTypeResponse(...)
    except InvalidInputError as e:
        raise HTTPException(422, detail=str(e))

@router.patch("/{id}", response_model=ReportTypeResponse)
def update_report_type(
    id: str,
    body: ReportTypeUpdate,
    current_user: User = Depends(require_role("admin")),
    report_type_repo=Depends(get_report_type_repo),
):
    try:
        rt = UpdateReportType(report_type_repo).execute(id, body.name, body.description)
        return ReportTypeResponse(...)
    except ReportTypeNotFoundError as e:
        raise HTTPException(404, detail=str(e))
    except InvalidInputError as e:
        raise HTTPException(422, detail=str(e))

@router.delete("/{id}", status_code=204)
def delete_report_type(
    id: str,
    current_user: User = Depends(require_role("admin")),
    report_type_repo=Depends(get_report_type_repo),
):
    try:
        DeleteReportType(report_type_repo).execute(id)
    except ReportTypeNotFoundError as e:
        raise HTTPException(404, detail=str(e))
```

Then modify `main.py` to include the new router:
```python
from fala_gavea.presentation.api.routers import report_types as report_types_router
# ...
app.include_router(report_types_router.router, prefix="/report_types", tags=["report_types"])
```

- **Files**: `src/fala_gavea/presentation/api/routers/report_types.py` (create), `src/fala_gavea/presentation/api/main.py` (modify)
- **References**: `product-design/project/standards.md § Backend §5, §8`, `product-design/project/constitution.md T2`
- **Depends on**: Step 1, Step 2
- **Interface**: Mounts at `/report_types`; 4 endpoints (GET public, POST/PATCH/DELETE admin)
- **Verify**: `uv run uvicorn fala_gavea.presentation.api.main:app` starts without import errors; `curl http://localhost:8000/openapi.json | python -m json.tool | grep report_types` shows the new routes
- **Tests**: Covered by Step 5
- [ ] Done

---

### Step 4: Seed script

Create `scripts/seed_report_types.py` -- a standalone script that bootstraps the 8 initial
ReportType records via the HTTP API (not direct SQL, to exercise the endpoint).

The script:
1. Reads `FALA_GAVEA_API_URL` (default `http://localhost:8000`) from env.
2. Reads `FALA_GAVEA_ADMIN_EMAIL` and `FALA_GAVEA_ADMIN_PASSWORD` from env (required).
3. Logs in via `POST /auth/token` (form-encoded). If the admin user does not exist yet, prints
   an error and exits non-zero.
4. For each of the 8 types, calls `POST /report_types` with the JWT Bearer token.
   Skips gracefully if a 422 is returned (idempotency: name conflict is not a hard error for a seed).

8 initial types (name, description):
```
("Iluminacao publica",     "Postes apagados, falha na rede eletrica de logradouros")
("Transito e mobilidade",  "Sinalizacao, semaforos, transporte publico")
("Vandalismo",             "Depredacao de patrimonio publico ou privado")
("Espaco publico",         "Calcadas, pracas, parques, equipamentos urbanos")
("Lixo e conservacao",     "Acumulo de lixo, entulho, limpeza urbana")
("Seguranca e circulacao", "Pontos de risco, iluminacao de vias, seguranca viaria")
("Conflito social",        "Situacoes de conflito ou perturbacao da ordem publica")
("Outro",                  "Demandas que nao se enquadram nas categorias anteriores")
```

Usage:
```bash
FALA_GAVEA_ADMIN_EMAIL=admin@gavea.br FALA_GAVEA_ADMIN_PASSWORD=<pass> uv run python scripts/seed_report_types.py
```

The script uses only stdlib (`urllib.request`, `json`, `os`, `sys`) -- no httpx dependency needed.

- **Files**: `scripts/seed_report_types.py` (create)
- **References**: `product-design/project/product-design-as-intended.md §3 (Tipos de Problema Dinamicos)`
- **Depends on**: Step 3
- **Interface**: N/A (standalone script)
- **Verify**: With server running and admin user created, `uv run python scripts/seed_report_types.py` exits 0 and `curl http://localhost:8000/report_types` returns 8 items
- **Tests**: N/A (script is integration tooling, not tested in pytest suite)
- [ ] Done

---

### Step 5: Tests + admin_headers fixture

Add `admin_headers` fixture to `tests/conftest.py` (analogous to existing `agent_headers` --
create admin user directly in DB then get JWT via POST /auth/token).

Create `tests/test_report_types.py` with the following test cases:

1. **GET /report_types -- no auth -- returns empty list** when no types exist.
2. **GET /report_types -- returns only active types** -- create one active, one inactive (soft-deleted),
   verify response contains only the active one.
3. **POST /report_types -- admin -- creates type** -- POST with admin_headers; assert 201 and
   response has correct name, active=True, id set.
4. **POST /report_types -- non-admin -- 403** -- POST with citizen_headers; assert 403.
5. **POST /report_types -- unauthenticated -- 401** -- POST without auth; assert 401.
6. **POST /report_types -- invalid name (too short) -- 422** -- name="ab" (2 chars); assert 422.
7. **PATCH /report_types/{id} -- admin -- updates name** -- create via POST, PATCH name,
   verify GET returns updated name.
8. **PATCH /report_types/{id} -- not found -- 404** -- PATCH unknown id; assert 404.
9. **DELETE /report_types/{id} -- admin -- soft-deletes** -- create, DELETE, then GET /report_types
   must not include the deleted type; direct DB query confirms active=False.
10. **DELETE /report_types/{id} -- not found -- 404** -- DELETE unknown id; assert 404.

- **Files**: `tests/test_report_types.py` (create), `tests/conftest.py` (modify)
- **References**: `product-design/project/standards.md § Testing §2`
- **Depends on**: Step 3
- **Interface**: N/A
- **Verify**: `uv run pytest tests/test_report_types.py -v` all 10 tests pass; `uv run pytest` (full suite) still green
- **Tests**: This step IS the tests
- [ ] Done

---

## Review Log

Perspectives applied (Essential tier for light review):

| Perspective | Decision | Notes |
|-------------|----------|-------|
| SEC | Adopted | `require_role("admin")` on all write endpoints; GET is intentionally public per design-intent §4. No secrets in code. |
| API | Adopted | DELETE returns 204 (no body); PATCH uses partial update semantics. GET /report_types is at collection root, no auth. Standard status codes. |
| ARCH | Adopted | Use cases in `application/`, no SQLAlchemy in `application/` or `presentation/`. Router uses Depends() for DI. Layer boundaries per standards.md §2. |
| TEST | Adopted | 10 test cases cover: public GET, role enforcement (admin/citizen/unauth), validation errors, PATCH update, soft-delete behavior, 404 paths. |
| SEC (seed script) | Adopted | Admin credentials via env vars only; no hardcoded secrets. Script uses stdlib urllib (no extra dep). |

Deferred:
- **PERF**: N/A for PoC scale; `find_all_active` has no pagination. Deferred -- acceptable for initial implementation.
- **DATA**: ReportType names are not PII; no sensitive data concerns in this feature.
