# Progress -- Plan 000079

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 1 — Domain layer
Status: SUCCESS
Notes: `domain/repositories/__init__.py` already existed. IForwardingRepository and ForwardingFilters created following the same ABC+dataclass pattern as IReportRepository. ForwardingNotFoundError appended to exceptions.py. `get_forwarding_repo` and `require_any_role` added to dependencies.py; the forwarding repo import is deferred (inside the function body) to avoid a circular/missing-module error until the SQLAlchemy implementation is created in a later step. All domain imports verified OK.

### Step 2 — SQLAlchemy repository
Status: SUCCESS
Notes: `ForwardingModel` has fields: id, institution, proposed_solution, status (SAEnum string), agent_id, created_at, updated_at. `ForwardingReportModel` has composite PK (forwarding_id, report_id). `ForwardingStatus` is a `str` Enum so `.value` is already the raw string stored in the DB. The `_to_entity` helper converts cleanly with `ForwardingStatus(m.status)`. Import verified: `from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository` prints OK. Pattern mirrors `SQLAlchemyReportRepository` closely (same save upsert logic, same filter chaining with `select()`).

### Step 3 — Pydantic schemas
Status: SUCCESS
Notes: Created `src/fala_gavea/presentation/schemas/forwarding.py` with 5 schemas: `ReportSummary` (embedded report in response, uses `ConfigDict(from_attributes=True)`), `ForwardingCreate` (POST body with field validators for institution 3-200, proposed_solution 20-5000, and non-empty report_ids), `ForwardingUpdate` (PATCH partial body, validators handle `None` gracefully), `ForwardingStatusUpdate` (status-only patch), and `ForwardingResponse` (full detail response embedding `list[ReportSummary]`). Uses `from __future__ import annotations` + `ConfigDict` (Pydantic v2 style), matching existing schema conventions in `report.py`. Import verified OK.

### Step 4 — Use cases
Status: SUCCESS
Notes: Created `src/fala_gavea/application/use_cases/forwardings/` sub-package with 5 use cases. `InvalidInputError` takes a plain string message (no `id` field — it's a subclass of `DomainError` which is just `Exception`). `ReportStatus.encaminhado` is the correct enum value for transitioning reports on forwarding creation. `datetime.now(timezone.utc)` used throughout (not deprecated `datetime.utcnow()`). `ForwardingStatus` is a `str` Enum so `ForwardingStatus(status_str)` conversion raises `ValueError` on invalid values. No SQLAlchemy imports in any use case. All 5 use cases verified import OK.

### Step 5 — Router + tests
Status: SUCCESS
Notes: `agent_headers` fixture was already present in conftest.py (added by an earlier step). All 13 tests written TDD-style (red first, then router made them green). Key patterns: (1) `require_any_role("agent", "admin")` stored as module-level `_agent_or_admin` to avoid re-creating the dependency closure for each endpoint; (2) `PATCH /{id}/status` must be declared before `PATCH /{id}` in FastAPI to avoid route shadowing; (3) GET list uses Option A (GetForwarding per item) for report inclusion — acceptable N+1 for PoC; (4) status filter in GET list parsed manually to `ForwardingStatus` enum before constructing `ForwardingFilters` (FastAPI cannot auto-parse custom str-Enums from query params without an alias). Full suite 38/38 passed.
Patterns: Route ordering matters for overlapping PATCH paths — declare more specific paths (/{id}/status) before generic (/{id}). `Query(None, alias="status")` needed when the param name clashes with Python builtins or reserved names.
