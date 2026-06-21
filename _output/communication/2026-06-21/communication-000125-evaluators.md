# Communication 000125 | EVL | 2026-06-21 15:31 UTC | Evaluators

**Project:** fala-gavea
**Audience:** Professors and technical evaluators assessing project merit (INF2921/CIS2114 -- AI Systems Design 2026.1)
**Purpose:** Technical evaluation briefing -- architecture, design decisions, and feature delivery

---

## Executive Overview

fala-gavea is a civic demand management platform for urban safety in the Gavea district. Citizens register urban problems (location, type, urgency level); public agents create forwardings to responsible institutions; AI assists exploratory analysis through semantic search and natural language chat.

**The problem it solves:** Urban safety complaint workflows are typically handled through opaque, non-searchable systems. Citizens lack feedback visibility; agents lack tools to spot patterns across complaints; administrators cannot easily see demand clusters. fala-gavea addresses all three gaps in a single, role-differentiated platform.

**What distinguishes it technically:**
- Clean architecture enforced throughout (domain / application / infrastructure / presentation), with no layer violations
- AI layer is optional and gracefully degraded -- the system works without Ollama or Anthropic API configured
- Dual LLM backend: local-first (Ollama, `qwen3:8b`) with a drop-in switch to Anthropic API via a single env var
- Semantic search is public (no auth required), lowering the barrier for citizen-facing discovery
- Frontend is a single React 18 + Vite + TypeScript SPA served directly by FastAPI StaticFiles -- no separate deployment

---

## System Capabilities

### Delivered Endpoints (21 total)

| Domain | Endpoints | Auth |
|---|---|---|
| Auth | POST /auth/register, POST /auth/login | public |
| Report Types | GET, POST, PUT, DELETE /report-types | GET public, others admin |
| Reports | POST, GET, GET/:id, PUT/:id, DELETE/:id | citizen/agent/admin |
| Reports -- AI | GET /reports/search, GET /reports/:id/similar | public |
| Reports -- AI | GET /reports/topics | auth |
| Forwardings | POST, GET, GET/:id, PUT/:id, DELETE/:id | agent/admin |
| NL Chat | POST /nl/chat | agent/admin |
| Keywords | GET /reports/keywords | auth |

### AI and Semantic Layer

**Semantic search** uses ChromaDB with sentence-transformers (e5-small model, CPU-optimized for Railway deployment). Two public endpoints enable similarity search without requiring a login.

**Topic extraction** uses a TF-IDF keyword client wired in place of BERTopic -- a deliberate memory-efficiency trade-off made for Railway's constrained container environment. The BERTopic implementation exists and can be restored by swapping the registry entry.

**NL Chat** is a RAG-backed assistant. The pipeline retrieves semantically similar reports from ChromaDB, injects them as context, and sends the prompt to the configured LLM (Ollama by default; Anthropic API when `ANTHROPIC_API_KEY` is set). The switch is zero-code -- purely environment-driven.

---

## Architecture Overview

```
src/fala_gavea/
  domain/
    entities/          -- pure dataclasses, no framework dependencies
    repositories/      -- ABCs (interfaces) for persistence
    exceptions.py
  application/
    use_cases/         -- business logic; no direct DB or HTTP access
  infrastructure/
    database/          -- SQLAlchemy models, session, migrations
    repositories/      -- SQLAlchemy implementations of domain repos
    chromadb/          -- ChromaClient (semantic indexing + search)
    embeddings/        -- sentence-transformers registry (swappable models)
    ollama/            -- OllamaClient
    topics/            -- TfidfTopicsClient (BERTopic-compatible interface)
  presentation/
    api/
      routers/         -- FastAPI routers per entity
      dependencies.py  -- get_current_user, require_role (JWT decoding isolated here)
      main.py
    schemas/           -- Pydantic v2 request/response schemas
```

**Key design decisions:**

1. **No layer violations** -- use cases call repository interfaces, never SQLAlchemy sessions directly. Routers call use cases, never repositories directly.

2. **JWT auth isolated to dependencies.py** -- no router decodes a token; all auth goes through `get_current_user` and `require_role` dependency injectors.

3. **All LLM and vector-store calls isolated to infrastructure/** -- use cases receive results, not clients. This means the AI backend is fully substitutable without touching business logic.

4. **Swappable embeddings registry** -- the sentence-transformers model is resolved at startup from a registry, making model changes a one-line config edit.

5. **Soft-delete on ReportTypes** -- admin-managed types can be deactivated without cascading data loss.

### Data Model

```
User (id, email, password_hash, role: citizen|agent|admin)
ReportType (id, name, active, deleted_at)
Report (id, user_id, report_type_id, text[10-2000], lat, lon,
        urgency: alta|media|baixa, status: pendente|em_analise|encaminhado|resolvido)
Forwarding (id, agent_id, institution[3-200], proposed_solution[20-5000],
            status: aguardando_solucao|solucao_em_andamento|finalizado)
ForwardingReport (forwarding_id, report_id)  -- many-to-many
```

---

## Frontend Architecture

The React 18 + Vite + TypeScript SPA is compiled to `static/` and served by FastAPI `StaticFiles`. No separate Node.js server is needed in production.

**Main screens:**

- **WorkspacePage (/)** -- the primary exploration surface. A `FilterPanel` accepts type, urgency, status, date range, and a live semantic query field. Five swappable views: Mapa (react-leaflet), Tabela, Topicos, Similares, Chat.
- **ReportFormPage (/report)** -- citizen report submission with browser geolocation.
- **ForwardingsPage (/agent)** -- agent forwarding management dashboard.
- **AdminPage** -- CSV seed upload (reports + report types), database wipe tools.

The semantic query field in `FilterPanel` calls `GET /reports/search` on each keystroke with debounce, providing real-time semantic filtering without a full page reload.

---

## Deployment and Configuration

**Docker:** Multi-stage build. Build stage compiles the Vite SPA; runtime stage is a slim Python 3.13 image. The compiled frontend is copied into the runtime image -- single container, no sidecar.

**Railway:** Deployed on Railway with CPU-only torch (reduced image size), e5-small embeddings model (low memory footprint), and TF-IDF topics (avoids BERTopic's RAM spike at startup).

**Environment variables (key ones):**

| Variable | Purpose | Default |
|---|---|---|
| DATABASE_URL | SQLite path or connection string | sqlite:///./fala_gavea.db |
| FALA_GAVEA_OLLAMA_URL | Ollama server URL | http://localhost:11434 |
| FALA_GAVEA_OLLAMA_MODEL | Ollama model name | qwen3:8b |
| ANTHROPIC_API_KEY | Switches NL chat to Anthropic API when set | (unset = Ollama) |
| JWT_SECRET_KEY | HS256 signing secret | (required) |

---

## Trade-offs and Honest Limitations

| Area | Decision | Rationale |
|---|---|---|
| SQLite | Used instead of PostgreSQL | Sufficient for PoC scale; zero-config for course evaluation |
| TF-IDF topics | Replaces BERTopic in production | BERTopic requires ~1.5 GB RAM at startup; Railway free tier cannot absorb that |
| Ollama local | Default LLM backend | Avoids API costs during development; Anthropic API available as drop-in |
| JWT 24h expiry | No refresh token | Acceptable for PoC; refresh token flow is a clear next step |
| No pagination | List endpoints return all rows | Acceptable for demo dataset sizes; pagination is the obvious next step |

---

## Adoption Path (for Evaluators)

To run a local evaluation instance:

```bash
# 1. Clone and install
git clone <repo>
cd fala-gavea
uv sync --extra dev

# 2. Set required env var
export JWT_SECRET_KEY=any-secret-string

# 3. Start the API (serves frontend too)
uv run uvicorn fala_gavea.presentation.api.main:app --reload

# 4. Open http://localhost:8000
# Use AdminPage to seed data from CSV, then explore WorkspacePage
```

To evaluate with Anthropic-backed NL chat, add `ANTHROPIC_API_KEY=<key>` before starting the server.

To evaluate semantic search without Ollama, the `/reports/search` and `/reports/:id/similar` endpoints are public and require no LLM configuration.

**Test suite:**

```bash
uv run pytest           # backend tests
cd frontend && npm test # frontend tests (vitest)
```

---

## Summary Assessment

fala-gavea delivers a complete, role-differentiated civic platform with a functioning AI layer within a clean architecture. The primary technical achievements for evaluation are:

1. **Architecture discipline** -- clean separation enforced at every layer; no shortcuts taken for deadline pressure
2. **Dual-mode AI backend** -- local-first with zero-code cloud fallback; the seam is explicit and testable
3. **Memory-aware deployment** -- production constraints (Railway RAM limits) drove concrete architectural decisions (TF-IDF over BERTopic, e5-small over larger models), demonstrating operational awareness beyond the happy path
4. **Single-container deployment** -- frontend compiled into the Python image; one `docker run` starts the full stack
5. **Role-differentiated UX** -- citizen, agent, and admin flows are distinct and enforced at the API level, not just the UI level
