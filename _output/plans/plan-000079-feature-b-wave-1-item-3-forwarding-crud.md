# Plan 000079 | FEATURE-B fala-gavea | 2026-06-17 22:33 UTC | wave-1-item-3-forwarding-crud | Review: light
plan_format_version: 1

source: roadmap-000071 -- Wave 1, Item 3: Forwarding CRUD (agent creates encaminhamento from selected reports)

## Brief (verbatim)

roadmap 1 item 3

## Agent Interpretation

Implement Wave 1, Item 3 from roadmap-000071: the Forwarding CRUD API.

The `Forwarding` entity, `ForwardingModel`, and `ForwardingReportModel` were created in
plan-000073. This plan wires the full Forwarding API on top of that foundation:

1. Domain repository interface (`IForwardingRepository`) with `ForwardingFilters` dataclass.
2. `ForwardingNotFoundError` in domain exceptions.
3. `require_any_role` in dependencies to support endpoints open to agent AND admin.
4. SQLAlchemy repository implementation handling cascade (save forwarding, link reports,
   update report statuses) within a single transaction.
5. Pydantic schemas: `ForwardingCreate`, `ForwardingUpdate`, `ForwardingStatusUpdate`,
   `ReportSummary`, `ForwardingResponse`.
6. Five use cases: `CreateForwarding`, `GetForwarding`, `ListForwardings`,
   `UpdateForwarding`, `UpdateForwardingStatus`.
7. FastAPI router with 5 endpoints (all require agent or admin).
8. Integration tests covering creation, status transitions, validation, and filtering.

## Scope

Wave 1, Item 3 from roadmap-000071. Excludes:
- Frontend static pages (Item 4, Wave 1)
- ChromaDB / semantic search (Items 5-7, Wave 2)
- Admin-only forwarding management (all forwarding endpoints are agent+admin)

Depends on: Wave 0 Items 1 and 2 (domain entities, auth, report endpoints, report_types). The
`Report.save()` method already supports status updates, so no changes to the report layer.

## Files

### New files
- `src/fala_gavea/domain/repositories/forwarding_repository.py`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_forwarding_repository.py`
- `src/fala_gavea/presentation/schemas/forwarding.py`
- `src/fala_gavea/application/use_cases/forwardings/__init__.py`
- `src/fala_gavea/application/use_cases/forwardings/create_forwarding.py`
- `src/fala_gavea/application/use_cases/forwardings/get_forwarding.py`
- `src/fala_gavea/application/use_cases/forwardings/list_forwardings.py`
- `src/fala_gavea/application/use_cases/forwardings/update_forwarding.py`
- `src/fala_gavea/application/use_cases/forwardings/update_forwarding_status.py`
- `src/fala_gavea/presentation/api/routers/forwardings.py`
- `tests/test_forwardings.py`

### Modified files
- `src/fala_gavea/domain/exceptions.py` (add ForwardingNotFoundError)
- `src/fala_gavea/presentation/api/dependencies.py` (add get_forwarding_repo, require_any_role)
- `src/fala_gavea/presentation/api/main.py` (include forwardings router)

---

## Steps

### Step 1: Domain layer -- repository interface, exceptions, and dependencies

**`domain/exceptions.py`** (modify -- append):
```python
class ForwardingNotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Forwarding not found: {id}")
        self.id = id
```

**`domain/repositories/forwarding_repository.py`** (create):
```python
@dataclass
class ForwardingFilters:
    status: ForwardingStatus | None = None
    institution: str | None = None  # substring match
    agent_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None

class IForwardingRepository(ABC):
    @abstractmethod
    def save(self, forwarding: Forwarding) -> Forwarding: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Forwarding | None: ...

    @abstractmethod
    def find_all(self, filters: ForwardingFilters) -> list[Forwarding]: ...

    @abstractmethod
    def add_reports(self, forwarding_id: str, report_ids: list[str]) -> None:
        """Link reports to a forwarding (inserts ForwardingReport rows). Called
        after save(); caller must commit or be in same transaction."""

    @abstractmethod
    def get_report_ids(self, forwarding_id: str) -> list[str]: ...
```

**`presentation/api/dependencies.py`** (modify -- append two functions):
```python
def get_forwarding_repo(db: Session = Depends(get_db)) -> IForwardingRepository:
    return SQLAlchemyForwardingRepository(db)

def require_any_role(*roles: str):
    """Returns a dependency that raises 403 if current_user.role not in roles."""
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles required: {', '.join(roles)}",
            )
        return current_user
    return _check
```

- **Files**: `src/fala_gavea/domain/exceptions.py` (modify), `src/fala_gavea/domain/repositories/forwarding_repository.py` (create), `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **References**: `product-design/project/standards.md § Backend §3, §4, §5`, `product-design/project/constitution.md T2`
- **Interface**: Exports `ForwardingFilters`, `IForwardingRepository` (domain); `ForwardingNotFoundError` (exceptions); `get_forwarding_repo`, `require_any_role` (dependencies)
- **Verify**: `uv run python -c "from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository, ForwardingFilters; from fala_gavea.domain.exceptions import ForwardingNotFoundError"` succeeds
- **Tests**: Covered by Step 5
- [ ] Done

---

### Step 2: SQLAlchemy forwarding repository

Create `infrastructure/repositories/sqlalchemy_forwarding_repository.py`.

This is the only place in the codebase that touches `ForwardingReportModel`.
The `add_reports` method inserts rows into `forwarding_reports`. The `CreateForwarding`
use case calls `save()` then `add_reports()` in the same unit of work (same SQLAlchemy
session, single commit).

```python
class SQLAlchemyForwardingRepository(IForwardingRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, f: Forwarding) -> Forwarding:
        model = self._session.get(ForwardingModel, f.id)
        if model is None:
            model = ForwardingModel(
                id=f.id, institution=f.institution,
                proposed_solution=f.proposed_solution,
                status=f.status.value, agent_id=f.agent_id,
                created_at=f.created_at, updated_at=f.updated_at,
            )
            self._session.add(model)
        else:
            model.institution = f.institution
            model.proposed_solution = f.proposed_solution
            model.status = f.status.value
            model.updated_at = f.updated_at
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, id: str) -> Forwarding | None:
        model = self._session.get(ForwardingModel, id)
        return self._to_entity(model) if model else None

    def find_all(self, filters: ForwardingFilters) -> list[Forwarding]:
        stmt = select(ForwardingModel)
        if filters.status is not None:
            stmt = stmt.where(ForwardingModel.status == filters.status.value)
        if filters.institution is not None:
            stmt = stmt.where(ForwardingModel.institution.ilike(f"%{filters.institution}%"))
        if filters.agent_id is not None:
            stmt = stmt.where(ForwardingModel.agent_id == filters.agent_id)
        if filters.since is not None:
            stmt = stmt.where(ForwardingModel.created_at >= filters.since)
        if filters.until is not None:
            stmt = stmt.where(ForwardingModel.created_at <= filters.until)
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def add_reports(self, forwarding_id: str, report_ids: list[str]) -> None:
        for rid in report_ids:
            self._session.add(
                ForwardingReportModel(forwarding_id=forwarding_id, report_id=rid)
            )
        self._session.commit()

    def get_report_ids(self, forwarding_id: str) -> list[str]:
        stmt = select(ForwardingReportModel.report_id).where(
            ForwardingReportModel.forwarding_id == forwarding_id
        )
        return list(self._session.scalars(stmt).all())

    def _to_entity(self, m: ForwardingModel) -> Forwarding: ...  # maps model -> entity
```

Note: `ForwardingStatus` is `str, Enum` so `f.status.value == f.status` -- either form works.

- **Files**: `src/fala_gavea/infrastructure/repositories/sqlalchemy_forwarding_repository.py` (create)
- **References**: `product-design/project/standards.md § Backend §4`, `product-design/project/standards.md § Database`
- **Depends on**: Step 1
- **Interface**: Exports `SQLAlchemyForwardingRepository` implementing `IForwardingRepository`
- **Verify**: `uv run python -c "from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository"` succeeds
- **Tests**: Covered by Step 5
- [ ] Done

---

### Step 3: Pydantic schemas for Forwarding

Create `presentation/schemas/forwarding.py`:

**`ReportSummary`**: lightweight report for embedding in ForwardingResponse.
```python
class ReportSummary(BaseModel):
    id: str
    text: str
    urgency: str
    status: str
    report_type_id: str
    created_at: datetime
    model_config = {"from_attributes": True}
```

**`ForwardingCreate`**: request body for POST /forwardings.
```python
class ForwardingCreate(BaseModel):
    institution: str
    proposed_solution: str
    report_ids: list[str]  # minimum 1

    @field_validator("institution")
    @classmethod
    def institution_length(cls, v: str) -> str:
        v = v.strip()
        if not (3 <= len(v) <= 200):
            raise ValueError("institution must be 3-200 characters")
        return v

    @field_validator("proposed_solution")
    @classmethod
    def solution_length(cls, v: str) -> str:
        v = v.strip()
        if not (20 <= len(v) <= 5000):
            raise ValueError("proposed_solution must be 20-5000 characters")
        return v

    @field_validator("report_ids")
    @classmethod
    def report_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("report_ids must contain at least one report id")
        return v
```

**`ForwardingUpdate`**: body for PATCH /forwardings/{id}.
```python
class ForwardingUpdate(BaseModel):
    institution: str | None = None  # validated same as ForwardingCreate if provided
    proposed_solution: str | None = None
```
(Apply same length validators as ForwardingCreate, triggered only when value is not None.)

**`ForwardingStatusUpdate`**: body for PATCH /forwardings/{id}/status.
```python
class ForwardingStatusUpdate(BaseModel):
    status: str  # validated against ForwardingStatus enum values in use case
```

**`ForwardingResponse`**: full forwarding detail.
```python
class ForwardingResponse(BaseModel):
    id: str
    institution: str
    proposed_solution: str
    status: str
    agent_id: str
    reports: list[ReportSummary]
    created_at: datetime
    updated_at: datetime
```

- **Files**: `src/fala_gavea/presentation/schemas/forwarding.py` (create)
- **References**: `product-design/project/product-design-as-intended.md §2, §10`, `product-design/project/standards.md § Backend §8`
- **Depends on**: Step 1
- **Interface**: Exports `ForwardingCreate`, `ForwardingUpdate`, `ForwardingStatusUpdate`, `ReportSummary`, `ForwardingResponse`
- **Verify**: `uv run python -c "from fala_gavea.presentation.schemas.forwarding import ForwardingCreate, ForwardingResponse"` succeeds
- **Tests**: Covered by Step 5
- [ ] Done

---

### Step 4: Use cases

Create `application/use_cases/forwardings/` sub-package (5 use cases + `__init__.py`).
All use cases: no SQLAlchemy imports; only domain types, interfaces, and exceptions.

**`create_forwarding.py`** -- `CreateForwarding(forwarding_repo, report_repo)`:
```
execute(institution, proposed_solution, report_ids, agent_id) -> tuple[Forwarding, list[Report]]:
    1. Strip and validate institution (3-200 chars).
    2. Strip and validate proposed_solution (20-5000 chars).
    3. Validate report_ids is non-empty.
    4. For each report_id: report_repo.find_by_id(); collect Report; raise InvalidInputError
       if any id not found ("Report not found: {id}").
    5. Create Forwarding(id=uuid4(), institution, proposed_solution,
         status=ForwardingStatus.aguardando_solucao, agent_id, now, now).
    6. forwarding_repo.save(forwarding).
    7. forwarding_repo.add_reports(forwarding.id, report_ids).
    8. Update each report: report.status = ReportStatus.encaminhado; report_repo.save(report).
    9. Return (forwarding, reports).
```

**`get_forwarding.py`** -- `GetForwarding(forwarding_repo, report_repo)`:
```
execute(id) -> tuple[Forwarding, list[Report]]:
    forwarding = forwarding_repo.find_by_id(id); raise ForwardingNotFoundError if None.
    report_ids = forwarding_repo.get_report_ids(id).
    reports = [report_repo.find_by_id(rid) for rid in report_ids]; filter None.
    return (forwarding, reports).
```

**`list_forwardings.py`** -- `ListForwardings(forwarding_repo)`:
```
execute(filters: ForwardingFilters) -> list[Forwarding]:
    return forwarding_repo.find_all(filters).
```

**`update_forwarding.py`** -- `UpdateForwarding(forwarding_repo)`:
```
execute(id, institution, proposed_solution) -> Forwarding:
    forwarding = find_by_id(id); raise ForwardingNotFoundError if None.
    if institution is not None: strip, validate 3-200, set forwarding.institution.
    if proposed_solution is not None: strip, validate 20-5000, set forwarding.proposed_solution.
    forwarding.updated_at = datetime.now(UTC).
    return forwarding_repo.save(forwarding).
```

**`update_forwarding_status.py`** -- `UpdateForwardingStatus(forwarding_repo)`:
```
execute(id, status_str) -> Forwarding:
    try:
        new_status = ForwardingStatus(status_str)
    except ValueError:
        raise InvalidInputError(f"status must be one of: aguardando_solucao, solucao_em_andamento, finalizado")
    forwarding = find_by_id(id); raise ForwardingNotFoundError if None.
    forwarding.status = new_status.
    forwarding.updated_at = datetime.now(UTC).
    return forwarding_repo.save(forwarding).
```

- **Files**: `src/fala_gavea/application/use_cases/forwardings/__init__.py` (create), `src/fala_gavea/application/use_cases/forwardings/create_forwarding.py` (create), `src/fala_gavea/application/use_cases/forwardings/get_forwarding.py` (create), `src/fala_gavea/application/use_cases/forwardings/list_forwardings.py` (create), `src/fala_gavea/application/use_cases/forwardings/update_forwarding.py` (create), `src/fala_gavea/application/use_cases/forwardings/update_forwarding_status.py` (create)
- **References**: `product-design/project/standards.md § Backend §4`, `product-design/project/product-design-as-intended.md §2 (Forwarding), §10`
- **Depends on**: Step 1, Step 2 (transitively -- use cases call repo methods defined there)
- **Interface**: Exports `CreateForwarding`, `GetForwarding`, `ListForwardings`, `UpdateForwarding`, `UpdateForwardingStatus` (each with `.execute()`)
- **Verify**: `uv run python -c "from fala_gavea.application.use_cases.forwardings.create_forwarding import CreateForwarding"` succeeds
- **Tests**: Covered by Step 5
- [ ] Done

---

### Step 5: Router + main.py registration + integration tests

**`presentation/api/routers/forwardings.py`** (create):

```
POST   /forwardings            require_any_role("agent","admin"); 201
GET    /forwardings            require_any_role("agent","admin"); query: status, institution, agent_id, since, until
GET    /forwardings/{id}       require_any_role("agent","admin")
PATCH  /forwardings/{id}       require_any_role("agent","admin")
PATCH  /forwardings/{id}/status require_any_role("agent","admin")
```

Response assembly for ForwardingResponse: call `GetForwarding.execute()` (or reuse result from
`CreateForwarding.execute()`) to get `(forwarding, reports)`, then build:
```python
ForwardingResponse(
    id=forwarding.id,
    institution=forwarding.institution,
    proposed_solution=forwarding.proposed_solution,
    status=forwarding.status.value,
    agent_id=forwarding.agent_id,
    reports=[ReportSummary(id=r.id, text=r.text, urgency=r.urgency.value,
               status=r.status.value, report_type_id=r.report_type_id,
               created_at=r.created_at) for r in reports],
    created_at=forwarding.created_at,
    updated_at=forwarding.updated_at,
)
```

Error mapping:
- `InvalidInputError` -> 422
- `ForwardingNotFoundError` -> 404
- Report id not found in CreateForwarding -> 422 (raised as InvalidInputError from use case)

`GET /forwardings` query parameters (use `Depends()` with a Pydantic model):
```python
class ForwardingFiltersQuery(BaseModel):
    status: str | None = None
    institution: str | None = None
    agent_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None
```
Map to `ForwardingFilters` in the router before calling `ListForwardings.execute()`.

**`main.py`** (modify): include `forwardings_router.router` at prefix `/forwardings`.

**`tests/test_forwardings.py`** (create):

Test cases (all use `agent_headers` fixture from conftest; use `admin_headers` where noted):

1. **POST /forwardings -- create with 2 reports** -- register citizen, create 2 reports, then
   agent creates forwarding linking them. Assert 201, `reports` has 2 items, both reports
   have `status=encaminhado` when fetched via GET /reports/{id}.

2. **POST /forwardings -- report_id not found -- 422** -- include a random UUID in report_ids;
   assert 422 with detail mentioning the unknown id.

3. **POST /forwardings -- empty report_ids -- 422** -- assert 422.

4. **POST /forwardings -- institution too short -- 422** -- institution="ab"; assert 422.

5. **POST /forwardings -- proposed_solution too short -- 422** -- len < 20; assert 422.

6. **POST /forwardings -- citizen role -- 403** -- use citizen_headers; assert 403.

7. **GET /forwardings -- returns created forwarding** -- create one, then GET; assert list
   contains the forwarding.

8. **GET /forwardings -- filter by status** -- create forwarding, filter by
   `status=aguardando_solucao`; assert it appears. Filter by `status=finalizado`; assert empty.

9. **GET /forwardings/{id} -- returns with reports list** -- create forwarding with 1 report;
   GET /{id}; assert `reports` has the linked report.

10. **GET /forwardings/{id} -- not found -- 404** -- GET unknown id; assert 404.

11. **PATCH /forwardings/{id}/status -- transitions to solucao_em_andamento** -- create
    forwarding, PATCH status; assert 200 with new status.

12. **PATCH /forwardings/{id}/status -- invalid status -- 422** -- status="xyz"; assert 422.

13. **PATCH /forwardings/{id} -- update institution** -- PATCH institution; assert GET returns
    updated value.

Note: `admin_headers` fixture is added by plan-000075 to `tests/conftest.py`. This plan
references it without re-adding it. Run `/implement plan-000075` before implementing this plan.

- **Files**: `src/fala_gavea/presentation/api/routers/forwardings.py` (create), `src/fala_gavea/presentation/api/main.py` (modify), `tests/test_forwardings.py` (create)
- **References**: `product-design/project/standards.md § Testing §2`, `product-design/project/product-design-as-intended.md §13 US-002, §15 JM-TB-002`
- **Depends on**: Step 3, Step 4
- **Interface**: Mounts at `/forwardings`; 5 endpoints (all agent+admin)
- **Verify**: `uv run pytest tests/test_forwardings.py -v` all 13 tests pass; full suite green
- **Tests**: This step IS the tests
- [ ] Done

---

## Review Log

Perspectives applied (Essential tier for light review):

| Perspective | Decision | Notes |
|-------------|----------|-------|
| SEC | Adopted | All 5 endpoints require `require_any_role("agent","admin")` -- citizens cannot create or view forwardings. Validation in use cases and Pydantic schemas. |
| API | Adopted | Two PATCH verbs on distinct paths (`/{id}` and `/{id}/status`) to distinguish partial update from status-machine transition. List endpoint uses query params via Depends(). 201 on POST, 200 on PATCH. |
| ARCH | Adopted | ForwardingRepository encapsulates ForwardingReport access -- no router or use case imports ForwardingReportModel. Use cases own the transaction logic (save + add_reports + update report statuses). |
| DATA | Adopted | `CreateForwarding` atomically transitions report statuses to `encaminhado`; validated in Step 5 test #1. A report can belong to multiple forwardings (roadmap D-D) -- no constraint prevents this. |
| TEST | Adopted | 13 test cases: role enforcement, CRUD paths, status transition, filtering, validation errors (missing report, empty list, field length), 404 paths. |

Deferred:
- **PERF**: `GetForwarding` fetches reports with N individual `find_by_id` calls. For PoC scale (handful of reports per forwarding) this is acceptable. A join query can replace it in a future optimization pass.
- **DATA (report in multiple forwardings)**: design intent D-D allows a report to appear in multiple forwardings. No guard against this in the use case. Acceptable for PoC; future enforcement if needed.
