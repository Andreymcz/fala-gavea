# DONE | 2026-06-24 09:35 UTC |
# Plan 000155 | feat/anon-backend | 2026-06-24 00:26 UTC | Anonymous reporting backend: token entity, CreateReport, query path, geo coarsen | Review: standard
plan_format_version: 1

source: roadmap-000151

## Brief

Implement the anonymous reporting backend: `AnonymousReportToken` SQLAlchemy repository, modify `CreateReport` use case to accept an `anonymous: bool` flag (returns a one-time UUID token when true, sets `author_id=None`), add a token-based query path to `ReportRepository`, and coarsen lat/lon in public API responses for anonymous reports.

## Context

Domain entity `AnonymousReportToken` and `IAnonymousTokenRepository` ABC defined in plan-000152. The key design: when a citizen submits with `anonymous=True`, the server generates a UUID token, hashes it (SHA-256), stores the hash in `anonymous_report_tokens`, and returns the plain UUID token once in the POST /reports response. The client stores the token in localStorage and uses it as a query parameter to retrieve their anonymous reports.

The "Meus relatos" feature already uses `author_id` filtering (D-012). For anonymous users, a parallel query path uses `anonymous_token_hash` lookup.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Token generation | `uuid.uuid4()` on the server | Unpredictable, unique; no client-supplied token accepted |
| Token storage | SHA-256 hex of the UUID; plaintext never stored | DB leak does not expose claim tokens |
| `author_id` on anonymous Report | `NULL` | Natural SQLAlchemy nullable; existing queries unaffected (they filter on non-null author_id) |
| Token returned in POST response | Once only | Client must store; server has no recovery path if lost (intentional) |
| Geo coarsening | Round lat/lon to 3 decimal places in response schemas when `author_id IS NULL` | ~110 m precision; mitigates re-identification in small community context |
| Public list endpoints | Anonymous reports included with coarsened coords | Transparency maintained; author not revealed |
| "Meus relatos" anonymous path | `GET /reports/mine?anonymous_token=<uuid>` (new endpoint) | Separate from the auth-required `POST /reports/query`; allows unauthenticated callers to retrieve their own reports |

## Steps

### Step 1: SQLAlchemy anonymous token repository

Implement `SQLAlchemyAnonymousTokenRepository` in `src/fala_gavea/infrastructure/repositories/anonymous_token_repository.py`:

- `save(token: AnonymousReportToken) -> AnonymousReportToken`: INSERT; raises if `report_id` already has a token (unique constraint)
- `find_report_ids_by_hash(token_hash: str) -> list[str]`: SELECT report_id WHERE token_hash=; returns list (typically one item)

Register `get_anon_token_repo()` in `presentation/api/dependencies.py`.

- **Files**: `src/fala_gavea/infrastructure/repositories/anonymous_token_repository.py` (create), `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **Tests**: `tests/integration/test_anon_token_repository.py`
- [ ] Done

### Step 2: Modify CreateReport use case

In `src/fala_gavea/application/use_cases/reports/create_report.py`, add `anonymous: bool = False` parameter to `CreateReportRequest` (or the execute signature):

- If `anonymous=False` (default): behavior unchanged — `author_id = current_user.id`.
- If `anonymous=True`: set `author_id = None`; after saving the report, generate `token = str(uuid4())`; compute `token_hash = sha256(token.encode()).hexdigest()`; save `AnonymousReportToken(report_id=report.id, token_hash=token_hash)` via `IAnonymousTokenRepository`; return `(report, token)` tuple.

Update the return type of `CreateReport.execute()` to `tuple[Report, str | None]` where the second element is the claim token (plaintext UUID, `None` for authenticated submissions).

- **Files**: `src/fala_gavea/application/use_cases/reports/create_report.py` (modify)
- **Tests**: `tests/unit/use_cases/test_create_report_anonymous.py` — test that anonymous submission produces a non-null token and sets author_id=None; authenticated submission returns None token and sets author_id
- [ ] Done

### Step 3: POST /reports schema and router update

Add `anonymous: bool = False` to `CreateReportRequest` (Pydantic schema in `presentation/schemas/reports.py`).

Add `anonymous_claim_token: str | None = None` to `ReportResponse`. This field is populated only in the POST /reports response when `anonymous=True`; all other response usages leave it `None` (field will be omitted in JSON via `model_config = ConfigDict(exclude_none=True)` if not already set, or documented as intentionally `null` otherwise).

Update the `/reports` POST router handler in `presentation/api/routers/reports.py`:
- Accept `anonymous` from the request body
- Allow unauthenticated callers when `anonymous=True` (use `Optional[get_current_user]` dependency; if `anonymous=False` and no user, return 401)
- Pass `anonymous` to `CreateReport.execute()`
- Include `anonymous_claim_token` in the response when non-None

- **Files**: `src/fala_gavea/presentation/schemas/reports.py` (modify), `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- **Verify**: POST /reports with `{"anonymous": true, ...}` returns `{"id": "...", "anonymous_claim_token": "<uuid>", "lat": <rounded>, "lon": <rounded>, ...}`; second POST /reports returns no `anonymous_claim_token`
- **Tests**: `tests/integration/test_anonymous_report.py`
- [ ] Done

### Step 4: GET /reports/mine endpoint (token-based anonymous lookup)

Add a new endpoint `GET /reports/mine?anonymous_token=<uuid>` in `reports.py` router:

- No auth required (no `get_current_user` dependency)
- Validate that `anonymous_token` query param is present and non-empty; return 400 if absent
- Compute `token_hash = sha256(anonymous_token.encode()).hexdigest()`
- Call `IAnonymousTokenRepository.find_report_ids_by_hash(token_hash)` → list of report IDs
- Return empty list if no match (do not distinguish "wrong token" from "no reports" — prevents token enumeration)
- Hydrate reports via `IReportRepository.find_by_ids(report_ids)` (add this method to the port and SQLAlchemy repo if not present)
- Apply geo coarsening to response (lat/lon rounded to 3 decimal places)

- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify), `src/fala_gavea/domain/repositories/report_repository.py` (modify — add `find_by_ids`), `src/fala_gavea/infrastructure/repositories/report_repository.py` (modify)
- **Verify**: GET /reports/mine?anonymous_token=<valid-token> returns the submitted report with coarsened coords; wrong token returns empty list
- **Tests**: `tests/integration/test_anonymous_report.py` (extend)
- [ ] Done

### Step 5: Geo coarsening in public response schemas

In the GeoJSON endpoint (`GET /reports/geojson`) and any other public read that includes lat/lon, coarsen coordinates for reports with `author_id IS NULL`:

- In `SQLAlchemyReportRepository` or the GeoJSON use case, when building the GeoJSON feature for an anonymous report, round lat/lon to `round(value, 3)`.
- Apply the same rounding in `ReportResponse` serialization when the caller is unauthenticated or the report is anonymous (simplest: apply unconditionally to anonymous reports in the response mapper).
- Agent/admin authenticated reads of anonymous reports receive full-precision coords (they need it for territorial analysis).

- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify — GeoJSON feature builder), `src/fala_gavea/presentation/schemas/reports.py` (add geo_coarsen helper)
- **Tests**: `tests/integration/test_anonymous_report.py` (extend — verify coords are rounded in public response)
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000155 (anon-backend)
