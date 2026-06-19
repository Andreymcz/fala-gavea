---
designer_description: "I'm the as-coded mirror of what actually shipped in fala-gavea -- maintained by post-skill after each plan so drift against product-design-as-intended.md is always visible."
---

# AS-CODED — fala-gavea

<!-- maintained-by: Agent (post-skill); Agent classification since SEJA 2.8.4 -->

---

## Conceptual Design

### 1. Platform Purpose

Implemented as a FastAPI REST API. Entry point: `src/fala_gavea/presentation/api/main.py`.
Auth: JWT Bearer (PyJWT, HS256, 24h expiry). DB: SQLite via SQLAlchemy synchronous ORM.
Sixteen endpoints live: POST /auth/register, POST /auth/token, POST /reports, GET /reports/geojson, GET /reports/search (public),
GET /reports/{id}/similar (public), GET /reports/{id},
GET /report_types (public), POST /report_types (admin), PATCH /report_types/{id} (admin), DELETE /report_types/{id} (admin, soft-delete),
POST /forwardings (agent+admin), GET /forwardings (agent+admin), GET /forwardings/{id} (agent+admin),
PATCH /forwardings/{id} (agent+admin), PATCH /forwardings/{id}/status (agent+admin).
Seed scripts: `scripts/seed_report_types.py` bootstraps 8 initial types via HTTP API; `scripts/seed_users.py` inserts 3 dev users (admin/citizen01/agente) directly via SQLAlchemy (bypasses API role restriction); `scripts/seed_relatos.py` ingests CSV scenario files or built-in templates and replicates corpus with lat/lon+date jitter to reach `--count` (default 10 000) reports spanning the past 365 days, inserted directly into SQLite. CSV schema documented in `seeds/relatos/SCHEMA.md`.

### 2. Entity Hierarchy

All 5 entities implemented as pure Python dataclasses in `domain/entities/`:

```
User               (citizen | agent | admin)
  users table: id, email, password_hash, name, role, created_at
ReportType         (admin-managed)
  report_types table: id, name, description, active (bool), created_at
Report             (citizen demand)
  reports table: id, text, lat, lon, urgency, photo_url, report_type_id FK, author_id FK, status, created_at
Forwarding         (full CRUD -- agent+admin)
  forwardings table: id, institution, proposed_solution, status, agent_id FK, created_at, updated_at
  status: aguardando_solucao | solucao_em_andamento | finalizado
ForwardingReport   (join table, fully implemented)
  forwarding_reports table: forwarding_id FK, report_id FK (composite PK)
```

SQLAlchemy models in `infrastructure/database/models.py`. FK enforcement via PRAGMA foreign_keys=ON event listener in `session.py`.

### 3. Domain-Specific Concepts

ReportType is dynamic (table-managed, not hardcoded Enum). Full admin CRUD implemented (Item 2):
`CreateReportType`, `UpdateReportType`, `DeleteReportType` use cases in `application/use_cases/report_types/`.
DELETE is soft-delete (sets active=False); GET /report_types returns only active types.
Forwarding CRUD fully implemented (Item 3): `CreateForwarding`, `GetForwarding`, `ListForwardings`,
`UpdateForwarding`, `UpdateForwardingStatus` use cases in `application/use_cases/forwardings/`.
`CreateForwarding` atomically links reports and transitions their status to `encaminhado`.
`require_any_role("agent","admin")` guards all forwarding endpoints.
A report can belong to multiple Forwardings (many-to-many via ForwardingReport, per D-D).
AI semantic layer foundation (Wave 0, plan-000089): `chromadb`, `sentence-transformers`, `bertopic` added to `pyproject.toml`. Domain ports `IReportIndexer`, `ISemanticSearchPort`, `ITopicModelPort` in `domain/repositories/semantic_ports.py`. `EmbeddingProviderRegistry` in `infrastructure/embeddings/registry.py` (env-var configurable per purpose). `ChromaSearchClient` in `infrastructure/chromadb/chroma_search_client.py` implementing both indexer and search ports.
Ingestion hook (Wave 0, plan-000090): `CreateReport` use case accepts optional `IReportIndexer` (injected via `dependencies.py → get_report_indexer()`). After `report_repo.save()`, calls `indexer.index(report)` inside a try/except — failures log WARNING and do not abort report creation. `get_report_indexer()` is a module-level singleton that lazily initialises `ChromaSearchClient(SemanticConfig())`; returns `None` on ChromaDB failure so the server stays up. `scripts/backfill_semantic.py` indexes existing reports idempotently (`--force` re-indexes; `--batch-size` controls throughput).
Search endpoints (Wave 1, plan-000094): public `GET /reports/search?q=&n=` (use case `SearchReports`) and public `GET /reports/{id}/similar?n=` (use case `FindSimilarReports`). Both inject `ISemanticSearchPort` via `dependencies.py → get_semantic_search_port()`, which reuses the `get_report_indexer()` `ChromaSearchClient` singleton (embedding model loaded once). Use cases query the port for `(report_id, score)` tuples, hydrate each `Report` by id via `IReportRepository` (skipping vectorstore ids absent in SQLite), and return `ReportSearchResult` (ReportResponse + `score`). `/search` returns 422 on empty `q`; `/{id}/similar` returns 404 if the base report is missing (port self-excludes the base); both return 503 when ChromaDB is unavailable; `n` clamped to [1,50]. No direct ChromaDB access outside `infrastructure/` (CONVENTION_1).

### 4. Permission Model

JWT Bearer via PyJWT. Roles: citizen, agent, admin (UserRole enum).
`get_current_user` and `require_role` in `presentation/api/dependencies.py`.
Public endpoints: GET /reports/geojson, GET /reports/search, GET /reports/{id}/similar, POST /auth/register, POST /auth/token, GET /report_types.
Auth-required endpoints: POST /reports (any authenticated user), GET /reports/{id} (any authenticated user).
Admin-only endpoints: POST /report_types, PATCH /report_types/{id}, DELETE /report_types/{id}.
Agent+admin endpoints (via `require_any_role`): POST /forwardings, GET /forwardings, GET /forwardings/{id}, PATCH /forwardings/{id}, PATCH /forwardings/{id}/status.
`get_forwarding_repo` and `require_any_role` added to `presentation/api/dependencies.py`.

### 5. Content Authoring & Attribution

`author_id` in Report is always set from `current_user.id` (JWT payload), never from request body. This prevents impersonation.

### 6. Content Import & Export

GET /reports/geojson returns RFC 7946-compliant GeoJSON FeatureCollection. Coordinates: [lon, lat] per RFC 7946. Supports query filters: urgency, status, type_id, since, until, bbox.

### 7. User Community & Localization

Monolingual pt-BR by design (PoC). Error messages in English (FastAPI default); localization is future work.

### 8. User Experience Patterns (Domain-Driven)

Implemented as a React 18 + Vite + TypeScript SPA (`frontend/`). Built to `static/` and served by FastAPI StaticFiles.

Screens:
- `/` — MapPage: Leaflet map centered on Gávea, urgency-colored DivIcon markers, FiltersSidebar (type/urgency/status/date), empty state message. Agent/admin users see multi-select checkboxes and SelectionBar → CreateForwardingDialog. Wave-2 placeholders: disabled semantic search input + chat affordance.
- `/report` — ReportFormPage: report-type Select, urgency Select (color-coded), text Textarea (10–2000 chars), geolocation button (`navigator.geolocation`), lat/lon inputs, optional photo_url. RequireAuth guard.
- `/agent` — ForwardingsPage: table of forwardings with expandable rows (linked reports), inline StatusSelect, status filter. RequireAuth roles=[agent,admin].
- `/login`, `/register` — Auth forms; JWT stored in localStorage.

All journey steps JM-TB-001 and JM-TB-002 are now implemented end-to-end (frontend + backend).

### 9. Administrative Domain

_Not yet implemented._

### 11. Deployment & Infrastructure

Containerized via multi-stage Dockerfile (node:22-alpine builds React SPA → python:3.13-slim runtime installs deps via `uv sync --frozen --no-dev`). `/data` is the persistent volume mount point.

Runtime configuration is fully env-var driven:
- `DATABASE_URL` — SQLite path (`sqlite:////data/fala_gavea.db` on Railway; relative default locally)
- `CHROMA_DATA_DIR` — ChromaDB persistence dir (checked before `FALA_GAVEA_VECTORSTORE_PATH`; default `./chroma_data`)
- `JWT_SECRET` — HMAC signing key
- `FALA_GAVEA_OLLAMA_URL` / `FALA_GAVEA_OLLAMA_MODEL` — optional; unset disables NL chat (returns 503)

`GET /health` (unauthenticated, excluded from OpenAPI schema) returns `{"status": "ok"}` — used by Railway health checks.

Ollama graceful degradation: `OllamaClient._available = False` when `FALA_GAVEA_OLLAMA_URL` is unset; `OllamaUnavailableError` (domain exception) is raised on any method call; `POST /nl/chat` router catches it and returns HTTP 503 with `{"detail": "NL chat is unavailable in this deployment."}`.

`railway.json` declares Dockerfile builder, `$PORT` start command, `/health` healthcheck (30s timeout), ON_FAILURE restart policy.

### 10. Validation Constants (Domain)

Enforced at both Pydantic schema layer AND use-case layer:
- Report.text: 10-2000 chars
- Report.lat: -90.0 to 90.0
- Report.lon: -180.0 to 180.0
- User.name: 2-100 chars
- User.email: EmailStr (pydantic-email-validator)
- JWT access token expiry: 24h (JWT_EXPIRY_HOURS env var, default 24)
- Report.urgency: alta | media | baixa
- Report.status: pendente | em_analise | encaminhado | resolvido (default: pendente)
- ReportType.name: 3-100 chars (trimmed; enforced in both `ReportTypeCreate` schema and `CreateReportType`/`UpdateReportType` use cases)
- Forwarding.institution: 3-200 chars (trimmed; enforced in `ForwardingCreate`/`ForwardingUpdate` schemas and `CreateForwarding`/`UpdateForwarding` use cases)
- Forwarding.proposed_solution: 20-5000 chars (trimmed; same enforcement layers)
- Forwarding.report_ids: non-empty list required on creation
- Forwarding.status: aguardando_solucao | solucao_em_andamento | finalizado

---

## Metacommunication

### 1. Global Metacommunication Summary

_Not yet implemented._

### 2. Extended Metacommunication Template Guiding Questions

_Not yet implemented._

### 3. Solution Representations (Implemented)

_Not yet implemented._

### 4. Per-Feature Metacommunication Log

_Not yet implemented._

### 5. Changelog

#### v2 — 2026-06-19
- **Added**: §11 Deployment & Infrastructure — Dockerfile (multi-stage), `railway.json`, `/health` endpoint, `CHROMA_DATA_DIR` env var, Ollama graceful degradation (`OllamaUnavailableError` → 503)
- **Source**: agent (post-skill)
- **Plan**: plan-000096

#### v1 — 2026-06-17 20:07 UTC

- **Initial**: Baseline as-coded record created (greenfield — no code implemented yet)
- **Source**: human (design, /design roadmap 1 item 1c)

---

## Journey Maps

### Delta from As-Intended

#### Not Yet Implemented

_N/A -- todas as jornadas projetadas estao implementadas._

#### Fully Implemented (as of plan-000082)

| Journey (JM-TB-NNN) | Steps | Notes |
|---------------------|-------|-------|
| JM-TB-001 | 1-7 (todos os steps do cidadao) | ReportFormPage com geolocalizacao, select tipo/urgencia, textarea, photo_url, POST /reports, redirect para mapa com novo marcador. |
| JM-TB-002 | 1-7 (todos os steps do agente) | MapPage com FiltersSidebar, checkboxes, SelectionBar, CreateForwardingDialog, ForwardingsPage com StatusSelect. |

#### Differs from Intent

_N/A -- nenhuma divergencia de intencao identificada._

### Changelog

#### v1 — 2026-06-17 20:07 UTC

- **Added**: Baseline as-coded record (greenfield)
- **Source**: agent (post-skill)
- **Plan**: design-roadmap-1-item-1c

#### v2 -- 2026-06-17

- **Added**: Sections 1-7, 10 (Conceptual Design) -- Wave 0 Item 1 backend implemented
- **Added**: Journey Maps delta updated -- JM-TB-001 partially implemented (backend only)
- **Source**: agent (post-skill)
- **Plan**: plan-000073

#### v3 -- 2026-06-17

- **Updated**: §1 Platform Purpose -- 9 endpoints live; seed script added
- **Updated**: §3 Domain-Specific Concepts -- ReportType CRUD implemented (use cases, router)
- **Updated**: §4 Permission Model -- admin endpoints wired; GET /report_types public
- **Updated**: §10 Validation Constants -- ReportType.name 3-100 chars added
- **Source**: agent (post-skill)
- **Plan**: plan-000075

#### v4 -- 2026-06-18

- **Updated**: §1 Platform Purpose -- 14 endpoints live (5 new forwarding endpoints)
- **Updated**: §2 Entity Hierarchy -- Forwarding and ForwardingReport fully implemented (CRUD, not stubs)
- **Updated**: §3 Domain-Specific Concepts -- Forwarding CRUD use cases; report status transition on create; require_any_role
- **Updated**: §4 Permission Model -- agent+admin forwarding endpoints wired; get_forwarding_repo added
- **Updated**: §10 Validation Constants -- Forwarding.institution, proposed_solution, report_ids, status
- **Updated**: Journey Maps -- JM-TB-002 partially implemented (backend); Partially Implemented table updated
- **Source**: agent (post-skill)
- **Plan**: plan-000079

#### v5 -- 2026-06-18

- **Updated**: §8 User Experience Patterns -- SPA implemented (React+Vite+TS, 4 screens, journeys JM-TB-001 + JM-TB-002 complete)
- **Source**: agent (post-skill)
- **Plan**: plan-000082

#### v6 -- 2026-06-18

- **Updated**: §1 Platform Purpose -- seed scripts expanded: seed_users.py (direct-DB user seeding for admin/agent roles) and seed_relatos.py (CSV + synthetic corpus replication, 10k reports, 1-year date spread)
- **Source**: agent (post-skill)
- **Plan**: plan-000085
