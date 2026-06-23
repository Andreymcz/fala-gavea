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
The live REST surface includes: POST /auth/register, POST /auth/token, POST /reports, GET /reports/geojson, GET /reports/search (public),
GET /reports/{id}/similar (public), GET /reports/keywords (auth-required, TF-IDF K-means), GET /reports/{id},
POST /reports/query (auth-required, unified multi-value filter + semantic ranking + pagination),
GET /report_types (public), POST /report_types (admin), PATCH /report_types/{id} (admin), DELETE /report_types/{id} (admin, soft-delete),
POST /forwardings (agent+admin), GET /forwardings (agent+admin), GET /forwardings/{id} (agent+admin),
PATCH /forwardings/{id} (agent+admin), PATCH /forwardings/{id}/status (agent+admin),
POST /nl/chat (agent+admin, RAG-backed NL assistant),
POST /nl/filter (any authenticated user, 20 req/min per user, NL→filter dict via LLMFilterParser + ParseNLFilter use case; 503 when LLM unavailable, 429 on rate limit),
POST /admin/seed/relatos (admin-only, CSV file upload bulk-insert; returns {inserted, skipped, errors}),
POST /admin/seed/topicos (admin-only, CSV upload bulk-creates ReportTypes; returns {inserted, skipped, errors}),
DELETE /admin/seed/wipe (admin-only, clears all Reports+Forwardings+optionally ReportTypes from SQLite and ChromaDB; query param include_report_types; returns {wiped: {reports, forwardings, report_types}}).
Citizen-transparency reads (roadmap-000146): GET /forwardings/public (public, no auth; optional `status` query filter; returns PublicForwardingResponse list without `agent_id`), GET /forwardings/public/{id} (public; 404 if missing), GET /reports/{id}/forwardings (public; returns PublicForwardingResponse list of forwardings linking that report; 404 if the report is missing). Basket open-similars: POST /reports/similar-to-set (agent+admin via `_agent_or_admin`; body `{report_ids, n}`; returns set-similarity-ranked ReportSearchResult list via `FindSimilarToReportSet` use case; 503 when semantic search unavailable).
Seed scripts: `scripts/seed_report_types.py` bootstraps 8 initial types via HTTP API; `scripts/seed_users.py` inserts 3 dev users (admin/citizen01/agente) directly via SQLAlchemy (bypasses API role restriction); `scripts/seed_relatos.py` ingests CSV scenario files or built-in templates and replicates corpus with lat/lon+date jitter to reach `--count` (default 10 000) reports spanning the past 365 days, inserted directly into SQLite. CSV schema documented in `seeds/relatos/SCHEMA.md`. `scripts/seed_forwardings.py` (plan-000148) authenticates as dev agent, queries all `pendente` reports via `POST /reports/query`, draws a 50% random sample (seeded, reproducible), groups by `report_type_id`, maps to institution+proposed_solution via a static name map, and POSTs one `Forwarding` per sub-batch (default ≤ 20 reports); idempotency guard skips if forwardings already exist (`--force` overrides).

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
SavedFilter        (user-owned filter preset — plan-000139)
  saved_filters table: id (UUID4), owner_id FK→users, name (1–80 chars), body (JSON string), schema_ver, created_at, updated_at
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
BERTopic topic modeling (Wave 2, plan-000099): dormant since plan-000124. `BERTopicClient` in `infrastructure/topics/bertopic_client.py` and `bertopic` package remain installed but are never instantiated at startup. `get_topic_model_port()` in `dependencies.py` returns `None` unconditionally (BERTopic reserved for future fine-tuning). `GET /reports/topics` endpoint removed.
TF-IDF keyword extraction (plan-000124): `GET /reports/keywords?type_id=&urgency=&status=&since=&until=&bbox=&min_docs=3`. Requires authentication. Returns `KeywordListResponse{keywords: list[KeywordItem{cluster_id, terms, count}], total_reports}`. Implemented via `TfidfKeywordClient` (`infrastructure/topics/tfidf_keyword_client.py`): uses `sklearn.feature_extraction.text.TfidfVectorizer` + `sklearn.cluster.KMeans` (no embedding model). Returns 503 if unavailable; returns empty keywords list when corpus < `min_docs`. `get_keyword_extractor()` dependency in `dependencies.py` (fresh instance per request, no singleton). Reuses `GetTopicsForReports` use case and `ITopicModelPort.infer_topics()` abstraction. `_parse_bbox` helper extracted to reduce duplication with `/geojson` endpoint. Default embedding model changed from `intfloat/multilingual-e5-base` to `intfloat/multilingual-e5-small` (SemanticConfig default; `embed_model_topics` field removed). Dockerfile: `UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu` before `uv sync` forces CPU-only PyTorch wheels.
Unified query endpoint + semantic ranker (plan-000132): `POST /reports/query` (auth-required) accepts a JSON body with multi-value filters (`report_type_ids[]`, `urgencies[]`, `statuses[]`), `bbox`, `since`/`until`, `text` (ILIKE), `q` (semantic rank), `limit`/`offset`. SQL is the filter source of truth; ChromaDB is a ranker only. `rank(query, ids) -> dict[str, float]` added to `ISemanticSearchPort` (cosine similarity over arbitrary candidate ids, no metadata mirroring). `find_page(filters, *, limit, offset, order, candidate_cap)` added to `IReportRepository` and implemented in `SQLAlchemyReportRepository`. `QueryReports` use case orchestrates filter→rank→paginate: semantic path fetches up to `max_results` (500) candidates via SQL, ranks in-memory by cosine score, then paginates; recency path applies SQL ordering and pagination directly. Response envelope: `{items, total, limit, offset, ranked_by}`. `ReportFilters` plural fields replace single-value `report_type_id`/`urgency`/`status`; legacy `/geojson` and `/keywords` endpoints wrap their single-value params in singleton lists (no breaking change). Frontend `useFilteredReports` retargeted to the unified endpoint (single `queryReports` call replaces dual GeoJSON+semantic queries); hook returns `features` adapted from `items` and `count=total`.
RAG chat NL assistant (Wave 2, plan-000100): `ILLMClient` ABC added to `domain/repositories/semantic_ports.py`. `infrastructure/llm/` package with `OllamaAdapter` (wraps existing `OllamaClient`), `AnthropicClient` (Anthropic SDK), and `factory.py` (dispatches via `FALA_GAVEA_LLM_PROVIDER` env var, default `ollama`). `AnswerWithRag` use case in `application/use_cases/chat/`: retrieves top-5 semantic hits via `ISemanticSearchPort`, hydrates report text via `IReportRepository`, builds pt-BR context system prompt, calls `ILLMClient.complete()`, returns `RagAnswer(response, cited_report_ids)`. `POST /nl/chat` router (agent+admin) wires the use case via FastAPI dependency injection; returns 503 when LLM or semantic search is unavailable. `anthropic>=0.50` added to `pyproject.toml` (only loaded when provider=anthropic). Privacy: `FALA_GAVEA_LLM_PROVIDER=ollama` (default) keeps report text local; `anthropic` sends retrieved snippets to Anthropic API.
Citizen transparency + cesta de relatos (roadmap-000146): `author_id` added to `ReportFilters` and threaded through `find_page`/`/geojson`/`/query` (backed by an index on `reports.author_id`), powering a "Meus relatos" author filter (D-012). Public forwarding reads (D-011): `ListForwardings`/`GetForwarding` reused behind `PublicForwardingResponse` (omits `agent_id`) for `GET /forwardings/public`, `GET /forwardings/public/{id}`, and `GET /reports/{id}/forwardings` (via `ListForwardingsForReport` use case); POST/PATCH forwarding remain agent+admin. Basket open-similars (D-010, D-013): `FindSimilarToReportSet` use case ranks reports semantically similar to the selected set and filters to "open" reports, where **open = `ReportStatus.pendente` only** (D-010; `em_analise`/`encaminhado`/`resolvido` are not duplicate candidates), surfaced via `POST /reports/similar-to-set`.

### 4. Permission Model

JWT Bearer via PyJWT. Roles: citizen, agent, admin (UserRole enum).
`get_current_user` and `require_role` in `presentation/api/dependencies.py`.
Public endpoints: GET /reports/geojson, GET /reports/search, GET /reports/{id}/similar, POST /auth/register, POST /auth/token, GET /report_types, GET /forwardings/public, GET /forwardings/public/{id}, GET /reports/{id}/forwardings (citizen-transparency reads, roadmap-000146 / D-011 -- responses use PublicForwardingResponse without `agent_id`).
Auth-required endpoints: POST /reports (any authenticated user), GET /reports/{id} (any authenticated user), GET /reports/keywords (any authenticated user), POST /reports/query (any authenticated user).
Admin-only endpoints: POST /report_types, PATCH /report_types/{id}, DELETE /report_types/{id}, POST /admin/seed/relatos, POST /admin/seed/topicos, DELETE /admin/seed/wipe.
Agent+admin endpoints (via `require_any_role`): POST /forwardings, GET /forwardings, GET /forwardings/{id}, PATCH /forwardings/{id}, PATCH /forwardings/{id}/status, POST /nl/chat, POST /reports/similar-to-set (basket open-similars, roadmap-000146 / D-013).
NL filter endpoint (any authenticated user via `get_current_user`): POST /nl/filter (rate-limited 20/min per user via slowapi).
`get_forwarding_repo` and `require_any_role` added to `presentation/api/dependencies.py`.
Saved-filter endpoints (plan-000139, any authenticated user, owner-scoped via JWT): POST /saved-filters, GET /saved-filters, GET /saved-filters/{id}, PATCH /saved-filters/{id}, DELETE /saved-filters/{id}. `owner_id` always taken from `current_user.id`; non-owned resources return 404 (BOLA prevention, R9). `get_saved_filter_repo` added to `presentation/api/dependencies.py`.

### 5. Content Authoring & Attribution

`author_id` in Report is always set from `current_user.id` (JWT payload), never from request body. This prevents impersonation.

### 6. Content Import & Export

GET /reports/geojson returns RFC 7946-compliant GeoJSON FeatureCollection. Coordinates: [lon, lat] per RFC 7946. Supports query filters: urgency, status, type_id, since, until, bbox.

### 7. User Community & Localization

Monolingual pt-BR by design (PoC). Error messages in English (FastAPI default); localization is future work.

### 8. User Experience Patterns (Domain-Driven)

Implemented as a React 18 + Vite + TypeScript SPA (`frontend/`). Built to `static/` and served by FastAPI StaticFiles.

**Workspace grid pattern (plan-000104):** The `/` route now renders `WorkspacePage` — a left-rail filter panel + swappable center views (Mapa, Tabela, Tópicos, Similares, Chat). Filter state is managed by a Zustand store (`workspaceStore.ts`); react-query owns server cache. Views are toggled via `ViewToggleBar` (aria-pressed chips). Citizen/anonymous sees Mapa+Tabela; agent/admin sees all five. Cross-filter unified: `useFilteredReports` calls `POST /reports/query` as a single request combining structural filters + optional semantic `q`; the hook adapts returned `items` into GeoJSON features and exposes `count = total` from the envelope. No separate GeoJSON or semantic search calls.

**Cesta de relatos + citizen transparency (roadmap-000146):** The floating SelectionBar is removed; `selectedIds` is now surfaced as a first-class "Cesta" view (D-013). The Header carries a "Cesta de relatos" button with a live count badge (`selectedIds.size`) that calls `showView("cesta")`. `CestaView` (`features/workspace/views/CestaView.tsx`, lazy-loaded, `ViewId 'cesta'` in `ViewToggleBar`) pairs a map/table review of the selected reports with an open-similars panel (`POST /reports/similar-to-set`, agent+admin) and inline relato creation, feeding `CreateForwardingDialog`. FilterPanel gains a "Meus relatos" author toggle (D-012) backed by the new `author_id` field on `ReportFilters`/queries. Public-read surfaces (D-011) consume `GET /forwardings/public*` and `GET /reports/{id}/forwardings` for unauthenticated citizen transparency.

**Phase C NL filter assistant (plan-000140):** Section 4 of FilterPanel is now fully functional. `IFilterParser` port + `ParseError` dataclass in `domain/repositories/filter_ports.py`. `LLMFilterParser` in `infrastructure/llm/llm_filter_parser.py` wraps `ILLMClient.complete_with_timeout()` (8s timeout) with a JSON extraction + one repair retry. `ParseNLFilter` use case in `application/use_cases/nl/parse_nl_filter.py` strips unknown keys via `_ALLOWED_KEYS`, accumulates warnings. `POST /nl/filter` merged into `nl.py` router (alongside `/nl/chat`), rate-limited at 20/min per user via `slowapi`. Frontend: `postNLFilter(text, token)` in `frontend/src/api/nlFilter.ts` maps HTTP 429→`rate_limit`, 503→`unavailable`; `workspaceStore` extended with `nlSuggestion`/`nlWarnings` state + `setNLSuggestion`/`applyNLSuggestion` actions; Section 4 textarea submits on Enter/button, shows suggestion preview zone (NL suggestion chips + "Aplicar sugestão ao rascunho" / "Descartar"), and graceful degradation messages in pt-BR on error. **Never auto-applies** — user must click "Aplicar sugestão ao rascunho" to merge into draft.

**Phase B preset bar (plan-000139):** Section 1 of FilterPanel is now fully active. "Salvar" opens a popover with a name input (pre-filled from `draftFilterName` or auto-generated from active filter chip labels, truncated to 40 chars); "Confirmar" calls `POST /saved-filters` with the committed filters body; if a preset is loaded, "Atualizar" calls `PATCH /saved-filters/{id}`. "Carregar" opens a dropdown listing the user's saved filters via `GET /saved-filters` (react-query, staleTime 30s); each item loads the saved body into draft state and sets `loadedPresetName`/`loadedPresetId` in the store; trash icon calls `DELETE /saved-filters/{id}`. The preset name in the Section 1 header shows `loadedPresetName ?? "Sem filtro salvo"` with a `*` suffix when the loaded preset has been modified since loading (`isDirty()`). `workspaceStore` extended with `loadedPresetId: string | null` and `setLoadedPresetId`; `clearFilters` resets it.

**Phase A UI overhaul (plan-000137):** Staged filter model — `workspaceStore` now maintains two slices: `filters` (committed, read by views) and `draftFilters` (edited by the panel). `applyFilters()` copies draft to committed; `clearFilters()` resets both; `removeFilter(key)` and `setBbox(bbox)` write to both immediately (chip remove and map bbox are direct manipulations). `isDirty()` compares the two slices across all 7 filter keys. Panel is now `w-72` with four sections: (1) preset bar with `loadedPresetName` display and disabled Phase B placeholders, (2) `ActiveFilterChips` showing committed filters as removable chips, (3) draft controls with dirty indicator ("Filtros alterados"), Aplicar, and Limpar, (4) NL assistant footer placeholder (Phase C). `DateRangePresets` provides 6 preset buttons + custom date inputs. `WorkspacePage` has a draft-loss guard via `useBlocker` (react-router-dom v6) and `beforeunload`. TableView gains column sort (local, `SortKey` type), full-text Radix Dialog ("Ler relato"), pagination (PAGE_SIZE=50, reset on filter/sort change), score column (gated on `ranked_by === 'similarity'`), and density toggle. MapView replaces draw gesture with "Filtrar nesta área" button (reads `map.getBounds()`, commits bbox to both slices immediately). SPA catch-all guard in `main.py` returns 404 JSON for known API prefixes (`_API_PREFIXES` set) before serving `index.html`.

Screens:
- `/` — WorkspacePage: FilterPanel (w-72, four-section, draft/Apply model, collapsible), ActiveFilterChips, DateRangePresets, ViewToggleBar, view grid. Views: MapView ("Filtrar nesta área" + "Limpar área" buttons, react-leaflet-cluster, optional draw), TableView (column sort, full-text dialog, pagination, score column, density toggle), TopicsView renamed "Palavras-chave" tab (TF-IDF keyword clusters via `useKeywords` — agent+admin only, 503-resilient, ViewId `keywords`), SimilarsView (full-base search, persistent "fora do filtro" caption), ChatView (RAG, cited_report_ids as focusable buttons → setSimilarSeed), CestaView (selection basket: map/table review, open-similars via POST /reports/similar-to-set, inline creation). Header "Cesta de relatos" button with count badge replaces the former floating SelectionBar; CreateForwardingDialog rendered in workspace shell (isAgent gate).
- `/report` — ReportFormPage: report-type Select, urgency Select (color-coded), text Textarea (10–2000 chars), geolocation button (`navigator.geolocation`), lat/lon inputs, optional photo_url. RequireAuth guard.
- `/agent` — ForwardingsPage: table of forwardings with expandable rows (linked reports), inline StatusSelect, status filter. RequireAuth roles=[agent,admin].
- `/login`, `/register` — Auth forms; JWT stored in localStorage.

All journey steps JM-TB-001, JM-TB-002, and JM-TB-003 are now implemented end-to-end (frontend + backend).

### 9. Administrative Domain

Bootstrap admin user (plan-000109): `BootstrapAdminUser` use case in `application/use_cases/admin/bootstrap_admin_user.py` runs on every `create_app()` call after `create_tables()`. Reads env vars `FALA_GAVEA_ADMIN_EMAIL`, `FALA_GAVEA_ADMIN_PASSWORD`, `FALA_GAVEA_ADMIN_NAME` (default "Admin"). If any required var is missing or the email already exists, logs DEBUG and exits. Otherwise hashes the password via `PasswordService` and creates a user with role=admin. Solves the chicken-and-egg problem of needing an admin to call admin endpoints.

Bulk ReportType import (plan-000109): `BulkCreateReportTypes` use case in `application/use_cases/report_types/bulk_create_report_types.py`. Accepts list of dicts with `nome` + `descricao`; reuses `CreateReportType` for name validation (3-100 chars); skips duplicates via `find_by_name`. Returns `BulkReportTypeResult{inserted, skipped, errors}`.

Database wipe (plan-000109): `WipeDatabase` use case in `application/use_cases/admin/wipe_database.py`. Receives a raw SQLAlchemy `Session` (bulk DELETEs don't fit domain repo ABCs). Deletes `forwarding_reports → forwardings → reports` in FK order; optionally deletes `report_types` when `include_report_types=True`. Calls `indexer.delete_all()` (new method on `IReportIndexer` ABC + `ChromaSearchClient`) to clear the ChromaDB collection and re-initialise it. Preserves Users. Returns `WipeResult{reports, forwardings, report_types}`.

Enriched bulk Report import (plan-000113): `BulkCreateReports.execute` in `application/use_cases/reports/bulk_create_reports.py` resolves a per-row author from `user_id` (the only required column) instead of attributing every report to the logged-in admin. New accounts are auto-created and deduplicated by synthetic e-mail `{user_id}@seed.gavea.br` (name `Cidadão {user_id}`, role `citizen`, dev-only default password `changeme`; existing accounts are reused via `find_by_email` and never re-saved) with a local `author_cache` to avoid repeat lookups. Unknown `topico` is auto-created via `CreateReportType` (guarded against `InvalidInputError` for <3-char names → row skipped, batch continues). Fallbacks: missing/invalid lat/lon → random point in the Gávea bounding box (lat −22.975…−22.953, lon −43.235…−43.205); missing/invalid `data` → `now`; empty/invalid `urgency` → `media`. `POST /admin/seed/relatos` parses CSV columns `user_id, texto_relato, latitude, longitude, data, topico, urgency` (accepts `id_cidadao` as a `user_id` alias) and injects `get_user_repo`/`get_password_service`. The admin panel (`/admin`, `AdminPage.tsx`) gained a "Seed de Relatos" card (CSV upload + pt-BR rules block) calling `api.seedRelatos(file)`. Report duplication on re-run is accepted (only users are deduplicated).

Enriched bulk Report import (plan-000113): `BulkCreateReports.execute` updated; see plan-000113 entry above.

Batch indexing performance (plan-000120): `IReportIndexer` gained `index_many(reports, batch_size=64)` with an ABC default-body fallback (loop over `index`) so existing mocks and test doubles are unaffected. `ChromaSearchClient.index_many` encodes all texts in a single `model.encode([...], batch_size=64)` forward pass and calls `collection.add()` once per invocation — eliminating N separate encode/add cycles. `reindex_all` similarly vectorised. `BulkCreateReports.execute` accumulates saved `Report` objects into `pending_index` and flushes via `index_many` every 500 reports (`CHUNK_SIZE=500`); removes the per-row `indexer.index()` call; indexing failures log ERROR with report IDs but do not abort (reports are already persisted in SQL).

Env vars for admin bootstrap: `FALA_GAVEA_ADMIN_EMAIL`, `FALA_GAVEA_ADMIN_PASSWORD`, `FALA_GAVEA_ADMIN_NAME`.

### 11. Deployment & Infrastructure

Containerized via multi-stage Dockerfile (node:22-alpine builds React SPA → python:3.13-slim runtime installs deps via `uv sync --frozen --no-dev`). `/data` is the persistent volume mount point.

Runtime configuration is fully env-var driven:
- `DATABASE_URL` — SQLite path (`sqlite:////data/fala_gavea.db` on Railway; relative default locally)
- `CHROMA_DATA_DIR` — ChromaDB persistence dir (checked before `FALA_GAVEA_VECTORSTORE_PATH`; default `./chroma_data`)
- `JWT_SECRET` — HMAC signing key
- `FALA_GAVEA_OLLAMA_URL` / `FALA_GAVEA_OLLAMA_MODEL` — optional; unset disables NL chat (returns 503)
- `FALA_GAVEA_LLM_PROVIDER` — `ollama` (default) or `anthropic`; selects `ILLMClient` implementation at startup
- `ANTHROPIC_API_KEY` — required when `FALA_GAVEA_LLM_PROVIDER=anthropic`; raises `EnvironmentError` on startup if unset
- `FALA_GAVEA_ANTHROPIC_MODEL` — Anthropic model id (default `claude-haiku-4-5-20251001`)

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

#### Workspace Grid (plan-000104)

**Designer Intent**: I give you a workspace where *you* decide how to read the relatos — the filter is yours and singular, and each view (map, table, topics, similars, chat) looks at the same set from different angles. The AI appears as just another lens of exploration, always citing where it drew its answers from — assistance, not decision.

**Implementation Status**: Implemented

**Last Updated**: 2026-06-19 | source: agent (post-skill)

### 5. Changelog

#### v3 — 2026-06-19
- **Added**: §4 Per-Feature Metacommunication Log — Workspace Grid entry (plan-000104)
- **Updated**: §4 Implementation Status → Implemented
- **Source**: agent (post-skill)
- **Plan**: plan-000104

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

#### Fully Implemented

| Journey (JM-TB-NNN) | Steps | Notes |
|---------------------|-------|-------|
| JM-TB-001 | 1-7 (todos os steps do cidadao) | ReportFormPage com geolocalizacao, select tipo/urgencia, textarea, photo_url, POST /reports, redirect para mapa com novo marcador. |
| JM-TB-002 | 1-7 (todos os steps do agente) | WorkspacePage → TableView checkboxes, SelectionBar, CreateForwardingDialog, ForwardingsPage com StatusSelect. (plan-000082: MapPage original; plan-000104: migrado para workspace com seleção via store) |
| JM-TB-003 | 1-8 (jornada de exploração/análise) | WorkspacePage: FilterPanel (cross-filter, busca semântica), MapView (clustered, bbox draw), TableView (seleção, similares), TopicsView (BERTopic), SimilarsView (fora do filtro), ChatView (RAG + cited_report_ids). (plan-000104) |

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

#### v7 -- 2026-06-22

- **Updated**: §1 Platform Purpose -- public citizen-transparency reads (GET /forwardings/public, /forwardings/public/{id}, /reports/{id}/forwardings) + POST /reports/similar-to-set (basket open-similars); removed stale "Nineteen endpoints" count label
- **Updated**: §3 Domain-Specific Concepts -- author_id ReportFilters ("Meus relatos"), PublicForwardingResponse public reads, FindSimilarToReportSet with open=pendente-only (D-010)
- **Updated**: §4 Permission Model -- public forwarding reads (D-011); agent+admin /reports/similar-to-set (D-013)
- **Updated**: §8 UX Patterns -- Cesta view + Header count badge replace floating SelectionBar; "Meus relatos" toggle (roadmap-000146)
- **Source**: agent (/explain spec-drift sync, research-000147)
- **Plan**: roadmap-000146 (D-010 -- D-013)
