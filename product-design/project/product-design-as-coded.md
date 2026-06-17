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
Five endpoints live: POST /auth/register, POST /auth/token, POST /reports, GET /reports/geojson, GET /reports/{id}.

### 2. Entity Hierarchy

All 5 entities implemented as pure Python dataclasses in `domain/entities/`:

```
User               (citizen | agent | admin)
  users table: id, email, password_hash, name, role, created_at
ReportType         (admin-managed)
  report_types table: id, name, description, active (bool), created_at
Report             (citizen demand)
  reports table: id, text, lat, lon, urgency, photo_url, report_type_id FK, author_id FK, status, created_at
Forwarding         (stub -- no endpoints yet)
  forwardings table: id, institution, proposed_solution, status, agent_id FK, created_at, updated_at
ForwardingReport   (stub -- no endpoints yet)
  forwarding_reports table: forwarding_id FK, report_id FK (composite PK)
```

SQLAlchemy models in `infrastructure/database/models.py`. FK enforcement via PRAGMA foreign_keys=ON event listener in `session.py`.

### 3. Domain-Specific Concepts

ReportType is dynamic (table-managed, not hardcoded Enum). No admin CRUD endpoints yet (Item 2).
Forwarding stub entity created; no CRUD API yet (Item 3).
AI assistance (ChromaDB/Ollama) not yet implemented (Items 5-7).

### 4. Permission Model

JWT Bearer via PyJWT. Roles: citizen, agent, admin (UserRole enum).
`get_current_user` and `require_role` in `presentation/api/dependencies.py`.
Public endpoints: GET /reports/geojson, POST /auth/register, POST /auth/token.
Auth-required endpoints: POST /reports (any authenticated user), GET /reports/{id} (any authenticated user).
Admin/agent endpoints: not yet wired (Items 2 and 3).

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
| JM-TB-002 | 1-7 (todos os steps do agente) | Backend nao implementado (forwardings, Item 3); frontend agent.html nao criado (Item 4) |

#### Partially Implemented

| Journey (JM-TB-NNN) | Step(s) Coded | Notes |
|---------------------|--------------|-------|
| JM-TB-001 | Step 7 (registro com status=pendente) | POST /reports cria relato; GET /reports/geojson expoe relatos publicamente. Frontend nao implementado. |

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
