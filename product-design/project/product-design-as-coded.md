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
Fourteen endpoints live: POST /auth/register, POST /auth/token, POST /reports, GET /reports/geojson, GET /reports/{id},
GET /report_types (public), POST /report_types (admin), PATCH /report_types/{id} (admin), DELETE /report_types/{id} (admin, soft-delete),
POST /forwardings (agent+admin), GET /forwardings (agent+admin), GET /forwardings/{id} (agent+admin),
PATCH /forwardings/{id} (agent+admin), PATCH /forwardings/{id}/status (agent+admin).
Seed script: `scripts/seed_report_types.py` bootstraps 8 initial types via the HTTP API.

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
AI assistance (ChromaDB/Ollama) not yet implemented (Items 5-7).

### 4. Permission Model

JWT Bearer via PyJWT. Roles: citizen, agent, admin (UserRole enum).
`get_current_user` and `require_role` in `presentation/api/dependencies.py`.
Public endpoints: GET /reports/geojson, POST /auth/register, POST /auth/token, GET /report_types.
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

_Not yet implemented (no frontend). See `product-design/project/product-design-as-intended.md §8`._

### 9. Administrative Domain

_Not yet implemented._

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

#### v1 — 2026-06-17 20:07 UTC

- **Initial**: Baseline as-coded record created (greenfield — no code implemented yet)
- **Source**: human (design, /design roadmap 1 item 1c)

---

## Journey Maps

### Delta from As-Intended

#### Not Yet Implemented

| Journey (JM-TB-NNN) | Step(s) | Gap Description |
|---------------------|---------|----------------|
| JM-TB-001 | 1 (formulario), 5 (geolocalizacao), 7 (redirect para mapa) | Backend implementado (POST /reports); frontend report.html nao criado ainda (Item 4) |
| JM-TB-001 | 2 (select tipo), 3 (urgencia), 4 (texto), 6 (photo_url) | API suporta todos os campos; form HTML nao implementado |
| JM-TB-002 | 1-7 (todos os steps do agente) | Frontend agent.html nao criado (Item 4); busca semantica/chat nao implementados (Items 5-7) |

#### Partially Implemented

| Journey (JM-TB-NNN) | Step(s) Coded | Notes |
|---------------------|--------------|-------|
| JM-TB-001 | Step 7 (registro com status=pendente) | POST /reports cria relato; GET /reports/geojson expoe relatos publicamente. Frontend nao implementado. |
| JM-TB-002 | Steps 5-7 (criar encaminhamento via API) | POST /forwardings cria encaminhamento, vincula relatos, transita status para encaminhado. GET /forwardings/{id} retorna com lista de relatos. Frontend agent.html nao implementado. |

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
