# DONE | 2026-06-17 21:10 UTC | Plan 000073 | FEATURE-B fala-gavea | 2026-06-17 20:17 UTC | wave-0-item-1-domain-auth-reports | Review: standard
plan_format_version: 1

source: roadmap-000071 -- Wave 0, Item 1: domain entities + auth + report endpoints

## Brief (verbatim)

roadmap 1 item 1 complete

## Agent Interpretation

Implement the complete scope of Wave 0 Item 1 from roadmap-000071.

The existing scaffold has a generic `Report` entity (TerritoryLevel-based) with basic CRUD, no
auth, and no domain model. This plan replaces it with the fala-gavea domain:

1. Replace the scaffold `Report` entity and create `User`, `ReportType`, `Forwarding`,
   `ForwardingReport` domain entities.
2. Add JWT Bearer auth: `POST /auth/register` and `POST /auth/token`.
3. Replace the generic reports endpoints with domain-specific ones: `POST /reports` (auth
   required, citizen+), `GET /reports/geojson` (public, with filters), `GET /reports/{id}`
   (auth required).
4. Replace the scaffold use cases with domain-specific ones, organized into `auth/` and
   `reports/` sub-packages.
5. Add integration tests: register + login flow, POST /reports, GET /reports/geojson filtering.

## Scope

Wave 0, Item 1 from roadmap-000071. Excludes:
- `GET /report_types` and ReportType CRUD admin endpoints (Item 2, Wave 0)
- Forwarding endpoints (Item 3, Wave 1)
- Frontend static pages (Item 4, Wave 1)
- ChromaDB / semantic search (Items 5-7, Wave 2)

The `Forwarding` and `ForwardingReport` domain entities and SQLAlchemy models ARE included
(they are part of the Item 1 entity scope), but no API endpoints are wired for them yet.

## Files

### New files
- `src/fala_gavea/domain/entities/user.py`
- `src/fala_gavea/domain/entities/report_type.py`
- `src/fala_gavea/domain/entities/forwarding.py`
- `src/fala_gavea/domain/repositories/user_repository.py`
- `src/fala_gavea/domain/repositories/report_type_repository.py`
- `src/fala_gavea/infrastructure/auth/__init__.py`
- `src/fala_gavea/infrastructure/auth/jwt_service.py`
- `src/fala_gavea/infrastructure/auth/password_service.py`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_user_repository.py`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_type_repository.py`
- `src/fala_gavea/application/use_cases/auth/__init__.py`
- `src/fala_gavea/application/use_cases/auth/register_user.py`
- `src/fala_gavea/application/use_cases/auth/login_user.py`
- `src/fala_gavea/application/use_cases/reports/__init__.py`
- `src/fala_gavea/application/use_cases/reports/create_report.py`
- `src/fala_gavea/application/use_cases/reports/list_reports_geojson.py`
- `src/fala_gavea/application/use_cases/reports/get_report.py`
- `src/fala_gavea/presentation/api/routers/auth.py`
- `src/fala_gavea/presentation/schemas/auth.py`
- `src/fala_gavea/presentation/schemas/report.py`
- `tests/test_auth.py`
- `tests/test_reports.py`

### Modified files
- `pyproject.toml`
- `src/fala_gavea/config.py`
- `src/fala_gavea/domain/entities/report.py`
- `src/fala_gavea/domain/entities/__init__.py`
- `src/fala_gavea/domain/repositories/report_repository.py`
- `src/fala_gavea/domain/exceptions.py`
- `src/fala_gavea/infrastructure/database/models.py`
- `src/fala_gavea/infrastructure/database/session.py`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py`
- `src/fala_gavea/presentation/api/dependencies.py`
- `src/fala_gavea/presentation/api/main.py`
- `src/fala_gavea/presentation/api/routers/reports.py`
- `tests/conftest.py`

### Deleted files
- `src/fala_gavea/application/use_cases/create_report.py`
- `src/fala_gavea/application/use_cases/delete_report.py`
- `src/fala_gavea/application/use_cases/get_report.py`
- `src/fala_gavea/application/use_cases/list_reports.py`
- `src/fala_gavea/presentation/schemas/report_schemas.py`
- `tests/integration/api/test_reports_api.py`
- `tests/unit/application/test_report_use_cases.py`

---

## Steps

### Step 1: Add PyJWT and passlib[bcrypt] dependencies

Add `pyjwt>=2.8` and `passlib[bcrypt]>=1.7` as runtime dependencies in `pyproject.toml`.
These are required for JWT token creation/validation and bcrypt password hashing respectively.
Also fix the DATABASE_URL default from `app.db` to `fala_gavea.db` in `config.py` to match
the design intent (constitution T4).
After modifying pyproject.toml, run `uv sync` to install the packages.

- **Files**: `pyproject.toml` (modify), `src/fala_gavea/config.py` (modify)
- **References**: `product-design/project/constitution.md T4`
- **Interface**: N/A
- **Verify**: `uv sync` exits 0; `uv run python -c "import jwt; import passlib"` succeeds
- **Tests**: N/A (no testable code changes)
- [x] Done

---

### Step 2: Rewrite domain entities

Replace the generic scaffold `Report` entity with the fala-gavea domain model. Create `User`,
`ReportType`, and `Forwarding` entities. Update domain exceptions. No SQLAlchemy imports allowed
in this layer.

**`domain/entities/report.py`** (replace): Remove TerritoryLevel. New fields:
`id: str`, `text: str`, `lat: float`, `lon: float`, `urgency: Urgency` (alta|media|baixa enum),
`photo_url: str | None`, `report_type_id: str`, `author_id: str`,
`status: ReportStatus` (pendente|em_analise|encaminhado|resolvido enum), `created_at: datetime`.
Factory: `Report.create(text, lat, lon, urgency, report_type_id, author_id, photo_url=None)`
-- generates UUID id, sets `status=ReportStatus.pendente`, `created_at=datetime.now(UTC)`.

**`domain/entities/user.py`** (create):
`id: str`, `email: str`, `password_hash: str`, `name: str`,
`role: UserRole` (citizen|agent|admin enum), `created_at: datetime`.
Factory: `User.create(email, password_hash, name, role=UserRole.citizen)`.

**`domain/entities/report_type.py`** (create):
`id: str`, `name: str`, `description: str | None`, `active: bool`, `created_at: datetime`.
No factory method needed (created by admin CRUD, scope Item 2).

**`domain/entities/forwarding.py`** (create -- stub entity, no endpoints yet):
`id: str`, `institution: str`, `proposed_solution: str`,
`status: ForwardingStatus` (aguardando_solucao|solucao_em_andamento|finalizado enum),
`agent_id: str`, `created_at: datetime`, `updated_at: datetime`.

**`domain/exceptions.py`** (extend -- keep `ReportNotFoundError` and `InvalidInputError`): Add
`UserNotFoundError`, `UserAlreadyExistsError`, `ReportTypeNotFoundError`,
`InvalidCredentialsError`, `PermissionDeniedError`.

- **Files**: `src/fala_gavea/domain/entities/report.py` (modify), `src/fala_gavea/domain/entities/user.py` (create), `src/fala_gavea/domain/entities/report_type.py` (create), `src/fala_gavea/domain/entities/forwarding.py` (create), `src/fala_gavea/domain/exceptions.py` (modify)
- **References**: `product-design/project/product-design-as-intended.md §2, §10`
- **Interface**: Exports `Report`, `Urgency`, `ReportStatus`, `User`, `UserRole`, `ReportType`, `Forwarding`, `ForwardingStatus` (dataclasses + enums). `Report.create(...)` and `User.create(...)` factory methods.
- **Verify**: `uv run python -c "from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus; from fala_gavea.domain.entities.user import User, UserRole"` imports cleanly without errors
- **Tests**: Covered by Step 10 (integration tests exercise entity creation via use cases)
- [x] Done

---

### Step 3: Domain repository interfaces

Update and create abstract base classes (ABCs) for persistence. These interfaces define what the
use cases need; they have no SQLAlchemy imports.

**`domain/repositories/report_repository.py`** (replace): Remove old generic methods.
New interface `IReportRepository(ABC)`:
- `save(report: Report) -> Report`
- `find_by_id(id: str) -> Report | None`
- `find_all(filters: ReportFilters) -> list[Report]`

`ReportFilters` dataclass (same module):
`report_type_id: str | None = None`, `urgency: Urgency | None = None`,
`status: ReportStatus | None = None`, `since: datetime | None = None`,
`until: datetime | None = None`,
`bbox: tuple[float, float, float, float] | None = None` (minLat, minLon, maxLat, maxLon).

**`domain/repositories/user_repository.py`** (create):
`IUserRepository(ABC)`:
- `save(user: User) -> User`
- `find_by_id(id: str) -> User | None`
- `find_by_email(email: str) -> User | None`

**`domain/repositories/report_type_repository.py`** (create):
`IReportTypeRepository(ABC)`:
- `find_by_id(id: str) -> ReportType | None`
- `find_all_active() -> list[ReportType]`
- `save(rt: ReportType) -> ReportType`

- **Files**: `src/fala_gavea/domain/repositories/report_repository.py` (modify), `src/fala_gavea/domain/repositories/user_repository.py` (create), `src/fala_gavea/domain/repositories/report_type_repository.py` (create)
- **References**: `product-design/project/standards.md § Backend §4`
- **Depends on**: Step 2
- **Interface**: Exports `IReportRepository`, `ReportFilters`, `IUserRepository`, `IReportTypeRepository`
- **Verify**: `uv run python -c "from fala_gavea.domain.repositories.user_repository import IUserRepository"` imports cleanly
- **Tests**: N/A (abstract interfaces -- no behavior to test in isolation)
- [x] Done

---

### Step 4: SQLAlchemy models -- all five tables

Replace the single `ReportModel` in `models.py` with all 5 tables required by the domain.
No domain entity imports in this file -- use string Enum values directly.
Also update `session.py` to add a `PRAGMA foreign_keys = ON` event listener (SQLite does not
enforce FK constraints by default).

**`users`** (`UserModel`): id String PK, email String unique not null, password_hash String not null,
name String not null, role SAEnum("citizen","agent","admin") not null, created_at DateTime not null.

**`report_types`** (`ReportTypeModel`): id String PK, name String not null, description String nullable,
active Boolean not null default True, created_at DateTime not null.

**`reports`** (`ReportModel`): id String PK, text String not null, lat Float not null, lon Float not null,
urgency SAEnum("alta","media","baixa") not null, photo_url String nullable,
report_type_id String FK->report_types.id not null, author_id String FK->users.id not null,
status SAEnum("pendente","em_analise","encaminhado","resolvido") not null default "pendente",
created_at DateTime not null.

**`forwardings`** (`ForwardingModel`): id String PK, institution String not null,
proposed_solution String not null,
status SAEnum("aguardando_solucao","solucao_em_andamento","finalizado") not null,
agent_id String FK->users.id not null, created_at DateTime not null, updated_at DateTime not null.

**`forwarding_reports`** (`ForwardingReportModel`): forwarding_id String FK->forwardings.id (PK part 1),
report_id String FK->reports.id (PK part 2). Composite PK.

`session.py` update: Add SQLAlchemy `event.listen` on engine connect to execute
`PRAGMA foreign_keys = ON` for SQLite connections.

- **Files**: `src/fala_gavea/infrastructure/database/models.py` (modify), `src/fala_gavea/infrastructure/database/session.py` (modify)
- **References**: `product-design/project/standards.md § Backend §9`
- **Depends on**: Step 2
- **Interface**: Exports `UserModel`, `ReportTypeModel`, `ReportModel`, `ForwardingModel`, `ForwardingReportModel`, `Base`
- **Verify**: `uv run python -c "from fala_gavea.infrastructure.database.models import Base; from sqlalchemy import create_engine; e = create_engine('sqlite:///:memory:'); Base.metadata.create_all(e)"` creates 5 tables without error
- **Tests**: Covered by Step 10 (conftest.py reset_db fixture exercises create_all)
- [x] Done

---

### Step 5: SQLAlchemy repository implementations

Implement the 3 repository interfaces. Each implementation converts between domain entities and
ORM models -- no ORM objects escape the infrastructure layer.

**`SQLAlchemyReportRepository`** (replace):
- `save(report) -> Report`: merge-or-add ReportModel; `_to_entity` / `_from_entity` helpers.
- `find_by_id(id) -> Report | None`: `session.get(ReportModel, id)` -> convert.
- `find_all(filters) -> list[Report]`: Dynamic `select(ReportModel)` with chained `.where()`
  clauses for each non-None filter field. Bbox filter: `lat BETWEEN minLat AND maxLat AND
  lon BETWEEN minLon AND maxLon`.

**`SQLAlchemyUserRepository`** (create):
- `save(user) -> User`
- `find_by_id(id) -> User | None`
- `find_by_email(email) -> User | None`: `select(UserModel).where(UserModel.email == email)`

**`SQLAlchemyReportTypeRepository`** (create):
- `find_by_id(id) -> ReportType | None`
- `find_all_active() -> list[ReportType]`: `select(ReportTypeModel).where(ReportTypeModel.active == True)`
- `save(rt) -> ReportType`

- **Files**: `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` (modify), `src/fala_gavea/infrastructure/repositories/sqlalchemy_user_repository.py` (create), `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_type_repository.py` (create)
- **References**: `product-design/project/standards.md § Backend §5`, `product-design/project/constitution.md T5`
- **Depends on**: Step 3, Step 4
- **Interface**: Exports `SQLAlchemyReportRepository`, `SQLAlchemyUserRepository`, `SQLAlchemyReportTypeRepository` (each implements its domain interface)
- **Verify**: `uv run python -c "from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository"` imports cleanly
- **Tests**: Covered by Step 10 (integration tests exercise the full stack including repos)
- [x] Done

---

### Step 6: Auth infrastructure -- JWTService and PasswordService

Create the auth infrastructure layer under `infrastructure/auth/`. This layer owns all auth
mechanics; no auth logic lives in use cases or routers.

**`infrastructure/auth/jwt_service.py`**:
```python
class JWTService:
    def create_access_token(user_id: str, role: str, expires_delta: timedelta) -> str
    def decode_token(token: str) -> dict  # raises InvalidCredentialsError on expired/invalid
```
Uses `PyJWT`: `jwt.encode(payload, key, algorithm)` / `jwt.decode(token, key, algorithms)`.
Payload: `{"sub": user_id, "role": role, "exp": datetime.now(UTC) + expires_delta}`.
On `jwt.ExpiredSignatureError` or `jwt.InvalidTokenError`, raise `InvalidCredentialsError`.
Reads `JWT_SECRET_KEY` from config (required); `JWT_ALGORITHM` (default HS256).

**`infrastructure/auth/password_service.py`**:
```python
class PasswordService:
    def hash_password(plain: str) -> str
    def verify_password(plain: str, hashed: str) -> bool
```
Uses `passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")`.

**`config.py`** update (extend Step 1):
Add `JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")`. The service raises
`ValueError("JWT_SECRET_KEY is not set")` at instantiation time if empty -- fail-fast per
constitution T3. Also add `JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")`
and `JWT_EXPIRY_HOURS: int = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))`.

- **Files**: `src/fala_gavea/infrastructure/auth/__init__.py` (create), `src/fala_gavea/infrastructure/auth/jwt_service.py` (create), `src/fala_gavea/infrastructure/auth/password_service.py` (create), `src/fala_gavea/config.py` (modify -- extends Step 1)
- **References**: `product-design/project/constitution.md S1, T1`, `product-design/project/standards.md § Backend §5, §7`
- **Depends on**: Step 1, Step 2
- **Interface**: `JWTService(secret_key, algorithm).create_access_token(user_id, role, expires_delta) -> str`, `JWTService.decode_token(token) -> dict`, `PasswordService().hash_password(plain) -> str`, `PasswordService().verify_password(plain, hashed) -> bool`
- **Verify**: `uv run python -c "from fala_gavea.infrastructure.auth.jwt_service import JWTService; from fala_gavea.infrastructure.auth.password_service import PasswordService"` imports cleanly
- **Tests**: Covered by Step 10 (auth integration tests exercise encode/decode indirectly)
- [x] Done

---

### Step 7: Application use cases -- auth and reports

Delete the 4 generic scaffold use cases. Create domain-specific use cases under `auth/` and
`reports/` sub-packages. Use cases receive their dependencies via constructor injection (no
imports from infrastructure in this layer -- only domain interfaces).

**Delete** (scaffold leftovers, no longer needed):
- `src/fala_gavea/application/use_cases/create_report.py`
- `src/fala_gavea/application/use_cases/delete_report.py`
- `src/fala_gavea/application/use_cases/get_report.py`
- `src/fala_gavea/application/use_cases/list_reports.py`

**Auth use cases** (`application/use_cases/auth/`):

`RegisterUser` (`register_user.py`):
Constructor: `(user_repo: IUserRepository, password_service: PasswordService)`.
`execute(email: str, password: str, name: str) -> User`:
- Validate `name` 2-100 chars; raise `InvalidInputError` otherwise.
- Call `user_repo.find_by_email(email)` -- raise `UserAlreadyExistsError` if not None.
- Hash password: `password_service.hash_password(password)`.
- Call `user_repo.save(User.create(email, hashed, name))`.
- Return saved User.

`LoginUser` (`login_user.py`):
Constructor: `(user_repo: IUserRepository, password_service: PasswordService, jwt_service: JWTService)`.
`execute(email: str, password: str) -> str` (returns JWT token string):
- Call `user_repo.find_by_email(email)` -- raise `InvalidCredentialsError` if None.
- Call `password_service.verify_password(password, user.password_hash)` -- raise `InvalidCredentialsError` if False.
- Return `jwt_service.create_access_token(user.id, user.role.value, timedelta(hours=config.JWT_EXPIRY_HOURS))`.

**Report use cases** (`application/use_cases/reports/`):

`CreateReport` (`create_report.py`):
Constructor: `(report_repo: IReportRepository, report_type_repo: IReportTypeRepository)`.
`execute(text, lat, lon, urgency, report_type_id, author_id, photo_url=None) -> Report`:
- Validate text 10-2000 chars; raise `InvalidInputError`.
- Validate lat in [-90, 90], lon in [-180, 180]; raise `InvalidInputError`.
- Call `report_type_repo.find_by_id(report_type_id)` -- raise `ReportTypeNotFoundError` if None or `active == False`.
- Call `report_repo.save(Report.create(...))`.

`ListReportsGeoJSON` (`list_reports_geojson.py`):
Constructor: `(report_repo: IReportRepository)`.
`execute(filters: ReportFilters) -> dict`:
- Call `report_repo.find_all(filters)`.
- Build GeoJSON FeatureCollection:
  `{"type": "FeatureCollection", "features": [feature_for(r) for r in reports]}`
  Each feature: `{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
  "properties": {"id": r.id, "text": r.text, "urgency": r.urgency.value, "status": r.status.value,
  "report_type_id": r.report_type_id, "created_at": r.created_at.isoformat()}}`.
  Note: GeoJSON coordinates are [longitude, latitude] per RFC 7946.

`GetReport` (`get_report.py`):
Constructor: `(report_repo: IReportRepository)`.
`execute(id: str) -> Report`:
- Call `report_repo.find_by_id(id)` -- raise `ReportNotFoundError` if None.

- **Files**: `src/fala_gavea/application/use_cases/auth/__init__.py` (create), `src/fala_gavea/application/use_cases/auth/register_user.py` (create), `src/fala_gavea/application/use_cases/auth/login_user.py` (create), `src/fala_gavea/application/use_cases/reports/__init__.py` (create), `src/fala_gavea/application/use_cases/reports/create_report.py` (create), `src/fala_gavea/application/use_cases/reports/list_reports_geojson.py` (create), `src/fala_gavea/application/use_cases/reports/get_report.py` (create)
- **Deleted files**: `src/fala_gavea/application/use_cases/create_report.py`, `src/fala_gavea/application/use_cases/delete_report.py`, `src/fala_gavea/application/use_cases/get_report.py`, `src/fala_gavea/application/use_cases/list_reports.py`
- **References**: `product-design/project/product-design-as-intended.md §10, §13`, `product-design/project/constitution.md T1, T5`
- **Depends on**: Step 3, Step 6
- **Interface**: `RegisterUser(user_repo, password_service).execute(email, password, name) -> User`; `LoginUser(user_repo, password_service, jwt_service).execute(email, password) -> str`; `CreateReport(report_repo, report_type_repo).execute(...) -> Report`; `ListReportsGeoJSON(report_repo).execute(filters) -> dict`; `GetReport(report_repo).execute(id) -> Report`
- **Verify**: Deleted files are gone; `uv run python -c "from fala_gavea.application.use_cases.auth.register_user import RegisterUser"` imports cleanly
- **Tests**: Covered by Step 10
- [x] Done

---

### Step 8: Pydantic schemas

Create auth schemas and replace the report schemas file (rename `report_schemas.py` -> `report.py`
to match the conventions table in `project/standards.md`).

**`presentation/schemas/auth.py`** (create):
- `RegisterRequest(email: EmailStr, password: str, name: str)`: `password` min 8 chars validator; `name` 2-100 chars.
- `LoginRequest(email: str, password: str)`.
- `TokenResponse(access_token: str, token_type: str = "bearer")`.
- `UserResponse(id: str, email: str, name: str, role: str, created_at: datetime)` -- no `password_hash`.

**`presentation/schemas/report.py`** (create -- content migrated from `report_schemas.py` + new):
- `ReportCreate(text: str, lat: float, lon: float, urgency: str, report_type_id: str, photo_url: str | None = None)`:
  Validators: text 10-2000 chars; lat must be in [-90, 90]; lon must be in [-180, 180];
  urgency must be in `{"alta", "media", "baixa"}`.
- `ReportResponse(id, text, lat, lon, urgency, status, report_type_id, author_id, photo_url, created_at)`.
  `model_config = {"from_attributes": True}`.
- `ReportFiltersQuery` -- used as FastAPI query parameters via `Depends`:
  `type_id: str | None = None`, `urgency: str | None = None`, `status: str | None = None`,
  `since: datetime | None = None`, `until: datetime | None = None`,
  `bbox: str | None = None` (string "minLat,minLon,maxLat,maxLon" -- parse in router).

**Delete** `src/fala_gavea/presentation/schemas/report_schemas.py` after content is migrated.

- **Files**: `src/fala_gavea/presentation/schemas/auth.py` (create), `src/fala_gavea/presentation/schemas/report.py` (create), `src/fala_gavea/presentation/schemas/report_schemas.py` (delete)
- **References**: `product-design/project/standards.md § Backend §8`, `product-design/project/product-design-as-intended.md §10`
- **Depends on**: Step 2
- **Interface**: Exports `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse`, `ReportCreate`, `ReportResponse`, `ReportFiltersQuery`
- **Verify**: `uv run python -c "from fala_gavea.presentation.schemas.auth import RegisterRequest; from fala_gavea.presentation.schemas.report import ReportCreate"` imports cleanly
- **Tests**: N/A (schema validation covered by integration tests in Step 10)
- [x] Done

---

### Step 9: API layer -- dependencies, auth router, reports router, main

Wire all dependency factories and update both routers. This is the integration layer; all
domain/use-case wiring happens here via FastAPI `Depends`.

**`presentation/api/dependencies.py`** (replace entirely):
```python
get_db() -> Generator[Session, None, None]          # yields SessionLocal session
get_user_repo(db=Depends(get_db)) -> IUserRepository
get_report_repo(db=Depends(get_db)) -> IReportRepository
get_report_type_repo(db=Depends(get_db)) -> IReportTypeRepository
get_password_service() -> PasswordService           # singleton-style
get_jwt_service() -> JWTService                     # reads config
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
get_current_user(token=Depends(oauth2_scheme), db=Depends(get_db)) -> User
    # decode JWT -> user_id; load user from repo; raise HTTP 401 if invalid/expired
require_role(role: str) -> Callable
    # returns a Depends factory that checks current_user.role == role, raises HTTP 403
```

**`presentation/api/routers/auth.py`** (create):
- `POST /register`: no auth; body `RegisterRequest`; calls `RegisterUser.execute`; returns `UserResponse` 201. Catch `UserAlreadyExistsError` -> HTTP 409.
- `POST /token`: no auth; form `OAuth2PasswordRequestForm`; calls `LoginUser.execute`; returns `TokenResponse` 200. Catch `InvalidCredentialsError` -> HTTP 401.

**`presentation/api/routers/reports.py`** (replace):
- `POST /`: `Depends(get_current_user)`; body `ReportCreate`; uses `current_user.id` as `author_id` (never from body); calls `CreateReport.execute`; returns `ReportResponse` 201.
  Catch `ReportTypeNotFoundError` -> HTTP 422; `InvalidInputError` -> HTTP 422.
- `GET /geojson`: no auth; query params `ReportFiltersQuery = Depends()`; parse `bbox` string into `tuple[float,float,float,float] | None`; calls `ListReportsGeoJSON.execute`; returns raw GeoJSON dict 200.
- `GET /{id}`: `Depends(get_current_user)`; calls `GetReport.execute`; returns `ReportResponse` 200. Catch `ReportNotFoundError` -> HTTP 404.

**`presentation/api/main.py`** (update):
Include `auth_router` at prefix `/auth` and `reports_router` at prefix `/reports`. Remove the
old generic reports router import.

- **Files**: `src/fala_gavea/presentation/api/dependencies.py` (modify), `src/fala_gavea/presentation/api/routers/auth.py` (create), `src/fala_gavea/presentation/api/routers/reports.py` (modify), `src/fala_gavea/presentation/api/main.py` (modify)
- **References**: `product-design/project/constitution.md T2`, `product-design/project/standards.md § Backend §5, §8`, `product-design/project/product-design-as-intended.md §4`
- **Depends on**: Step 6, Step 7, Step 8
- **Interface**: N/A (leaf step)
- **Verify**: `JWT_SECRET_KEY=test uv run uvicorn fala_gavea.presentation.api.main:app` starts without error; `GET /docs` lists `/auth/register`, `/auth/token`, `POST /reports`, `GET /reports/geojson`, `GET /reports/{id}`
- **Tests**: Covered by Step 10
- [x] Done

---

### Step 10: Tests

Update `conftest.py` and add two integration test modules. Remove obsolete scaffold tests.
All tests use SQLite in-memory. Set `JWT_SECRET_KEY=test-secret` in env before any import.

**`tests/conftest.py`** (replace):
- Set `os.environ["JWT_SECRET_KEY"] = "test-secret"` at top (before any app imports).
- Keep in-memory SQLite engine + StaticPool pattern (same as current).
- Keep `reset_db` autouse fixture.
- Add `db_session` fixture (same pattern as current).
- Add `client` fixture: `TestClient(app)` with `get_db` overridden to yield `db_session`.
- Add `citizen_token` fixture: POST /auth/register (email="citizen@test.com", password="pass1234", name="Test"); POST /auth/token -> return token string.
- Add `citizen_headers` fixture: `{"Authorization": f"Bearer {citizen_token}"}`.
- Add `agent_headers` fixture: Insert a User with role=agent directly via `SQLAlchemyUserRepository` (bypasses register default=citizen); login -> return headers. Needed for future Item 3+ tests.
- Add `sample_report_type` fixture: Insert a `ReportType` with `active=True` via `SQLAlchemyReportTypeRepository`; return its `id`.

**`tests/test_auth.py`** (create):
- `test_register_success`: POST /auth/register valid body -> 201, response has `id`, `email`, no `password_hash`.
- `test_register_duplicate_email`: register same email twice -> second returns 409.
- `test_register_short_name`: name="A" -> 422.
- `test_login_success`: register then POST /auth/token -> 200, `access_token` in response.
- `test_login_wrong_password`: POST /auth/token with wrong password -> 401.
- `test_login_unknown_email`: POST /auth/token with unregistered email -> 401.

**`tests/test_reports.py`** (create):
- `test_create_report_authenticated`: POST /reports with `citizen_headers` and valid body (text 15 chars, valid lat/lon, urgency="alta", report_type_id=`sample_report_type`) -> 201, response has `id`, `status="pendente"`, `author_id == citizen user id`.
- `test_create_report_unauthenticated`: POST /reports without auth header -> 401.
- `test_create_report_invalid_text_too_short`: text="short" (5 chars) -> 422.
- `test_create_report_invalid_report_type`: report_type_id="nonexistent" -> 422.
- `test_geojson_returns_feature_collection`: create a report; GET /reports/geojson (no auth) -> 200, `type == "FeatureCollection"`, `features` is list of len 1.
- `test_geojson_urgency_filter`: create reports with urgency=alta and urgency=baixa; GET /reports/geojson?urgency=alta -> only 1 feature returned.
- `test_get_report_authenticated`: create report; GET /reports/{id} with `citizen_headers` -> 200.
- `test_get_report_not_found`: GET /reports/nonexistent-id with `citizen_headers` -> 404.
- `test_get_report_unauthenticated`: GET /reports/{id} without auth -> 401.

**Delete**:
- `tests/integration/api/test_reports_api.py`
- `tests/unit/application/test_report_use_cases.py`

- **Files**: `tests/conftest.py` (modify), `tests/test_auth.py` (create), `tests/test_reports.py` (create)
- **Deleted files**: `tests/integration/api/test_reports_api.py`, `tests/unit/application/test_report_use_cases.py`
- **References**: `product-design/project/standards.md § Testing §1, §2, §3, §4`
- **Depends on**: Step 9
- **Interface**: N/A
- **Verify**: `uv run pytest` exits 0 with all tests green; no test imports the deleted scaffold use cases
- **Tests**: This step IS the tests
- [x] Done

---

## Review: standard

Review depth: standard (auto=standard for multi-entity multi-layer change; floor=light from conventions; flag=none; effective=standard).

### Perspectives evaluated

| Perspective | Tag | Status | Notes |
|-------------|-----|--------|-------|
| Security | SEC | Adopted | JWT HS256 via PyJWT; bcrypt via passlib; `JWT_SECRET_KEY` from env, raises at JWTService init if empty (fail-fast); `author_id` always taken from JWT claims, never from request body (prevents impersonation); `/reports/geojson` is intentionally public by design (constitution S3: semantic search is read-only) |
| Architecture | ARCH | Adopted | Domain layer stays pure -- no SQLAlchemy, PyJWT, or passlib imports in `domain/`; use cases depend only on domain interfaces + `PasswordService`/`JWTService` interfaces; infrastructure owns all ORM and auth mechanics (constitution T1, T5) |
| API Design | API | Adopted | GeoJSON FeatureCollection per RFC 7946 (coordinates: [lon, lat]); OAuth2PasswordRequestForm for `/auth/token` follows FastAPI + OAuth2 convention; consistent HTTP status codes (201 create, 401 unauth, 403 forbidden, 404 not found, 409 conflict, 422 validation) |
| Testability | TEST | Adopted | All tests use SQLite in-memory with StaticPool; auth tokens generated in-process; ChromaDB and Ollama not yet in scope (nothing to mock); `sample_report_type` fixture avoids hardcoded IDs |
| Database | DB | Adopted | SQLite FK enforcement via `PRAGMA foreign_keys = ON` event listener (Step 4); `create_all` at startup (no Alembic) is accepted for PoC per design intent D-003 and standards §9; no hard deletes (constitution T4 equivalent) |
| Data Integrity | DATA | Adopted | Validation constants from design-intent §10 enforced at both Pydantic schema layer AND use-case layer (double validation); `password_hash` excluded from all response models |
| Developer Experience | DX | Adopted | Config raises `ValueError` at `JWTService` instantiation for missing secret (fail-fast, not silent); FastAPI auto-generates `/docs` with all endpoints; error responses use standard `{"detail": "..."}` format |

### Deferred (N/A for this scope)

| Perspective | Tag | Reason |
|-------------|-----|--------|
| Internationalization | I18N | Monolingual pt-BR PoC by design; no i18n framework needed |
| Performance | PERF | PoC scale; GeoJSON filter query pushes predicates to SQLite; no N+1 risk in current shape |
| Compatibility | COMPAT | Greenfield -- no backward-compat concern |
| Responsive Design | RESP | Frontend scope (Item 4) |
| Visual Design | VIS | Frontend scope (Item 4) |
| Accessibility | A11Y | Frontend scope (Item 4) |
| Microinteractions | MICRO | Frontend scope (Item 4) |
| Operations / DevOps | OPS | Local dev only; uvicorn --reload; no prod deployment in scope |

---

## Notes

- The `static/` directory for frontend pages is NOT created in this plan. `FastAPI StaticFiles`
  is wired in Item 4 (Wave 1).
- `GET /report_types` (public list) is explicitly deferred to Item 2. The frontend form will
  call this endpoint once Item 2 is implemented. For Item 1 tests, `sample_report_type` is
  inserted directly via the repository fixture.
- Seed script for 8 initial ReportTypes (`scripts/seed_report_types.py`) is also Item 2 scope.
- The `ForwardingModel` and `ForwardingReportModel` are created in Step 4 to ensure the DB
  schema is complete. No wired endpoints yet -- those are Item 3.

---

## Execution Summary

**Completed:** 2026-06-17 21:10 UTC | Steps: 10/10 | Iterations: 10/20 | Tests: 15 passed, 0 failed

### Steps executed (commits)
| Step | Title | Commit | Status |
|------|-------|--------|--------|
| 1 | Add PyJWT and passlib[bcrypt] dependencies | 346658b | SUCCESS |
| 2 | Rewrite domain entities | 69ebb60 | SUCCESS |
| 3 | Domain repository interfaces | 460484a | SUCCESS |
| 4 | SQLAlchemy models -- all five tables | c15cb23 | SUCCESS |
| 8 | Pydantic schemas | 1820187 | SUCCESS |
| 6 | Auth infrastructure | 16dd3be | SUCCESS |
| 5 | SQLAlchemy repository implementations | d50f362 | SUCCESS |
| 7 | Application use cases -- auth and reports | 8272b11 | SUCCESS |
| 9 | API layer -- dependencies, routers, main | 8b83dbc | SUCCESS |
| 10 | Integration tests -- auth and reports | 816bcf3 | SUCCESS |

### Key learnings (from progress file)
- passlib 1.7.4 is incompatible with bcrypt 5.0.0 on this environment; `PasswordService` uses bcrypt directly.
- `InvalidCredentialsError` constructor in `domain/exceptions.py` takes no positional args -- fixed in Step 10.
- Test JWT secret "test-secret-key-for-testing" (27 bytes) triggers `InsecureKeyLengthWarning` from PyJWT; advisory only -- use a 32+ byte secret in production.
- `HTTP_422_UNPROCESSABLE_ENTITY` is deprecated in newer FastAPI; consider renaming to `HTTP_422_UNPROCESSABLE_CONTENT` in a future cleanup.

### Non-blocking warnings (quality gate)
- `httpx`/starlette deprecation -- test client; install httpx2 to silence.
- JWT key length < 32 bytes in test secret -- test-only concern.
- `HTTP_422_UNPROCESSABLE_ENTITY` deprecation -- advisory rename for future.

