# AS-CODED CHANGELOG — fala-gavea

### v21 -- 2026-06-26
- **Added**: Self-docs platform-helper RAG (plan-000177, D-014) — separate chat bounded context over the project's own docs (`_output/` + `product-design/`), distinct from relatos `/nl/chat`
- **Added**: `domain/repositories/doc_ports.py` (`DocChunk`/`DocSearchHit`/`IDocSearchPort`/`IDocIndexer`); `infrastructure/docs/markdown_chunker.py` (heading chunker + default-deny `role_visibility` classifier + secret guard + corpus walker); `infrastructure/chromadb/chroma_doc_search_client.py` (`ChromaDocSearchClient`, own `falagavea_selfdocs` collection + path, fail-closed role filter); `application/use_cases/help/answer_help_with_rag.py`; `POST /nl/help` (any auth user, role→visibility, 503, per-IP limit); `scripts/reindex_selfdocs.py`; frontend Header "Ajuda" modal (`features/help/HelpChat.tsx` + `api/helpChat.ts`)
- **Changed**: `SemanticConfig` (+`selfdocs_collection`/`selfdocs_corpus_roots`/`selfdocs_vectorstore_path`); `dependencies.py` (`get_embedding_model()` shared singleton, `get_doc_search_port()`); `ChromaSearchClient.__init__` accepts optional injected `model`; Dockerfile builds the self-docs index at build time into `/app/selfdocs_chroma` + `.dockerignore` re-includes corpus subdirs
- **Source**: agent (post-skill)
- **Plan**: plan-000177

### v20 -- 2026-06-25
- **Added**: `scripts/seed_citizen01.py` — creates 10 relatos as citizen01@gavea.br and 1 forwarding as agente linking citizen01's first 3 relatos plus up to 2 pendente reports from other users; idempotent via `GET /forwardings/mine` guard; `--force` override
- **Changed**: `scripts/seed_all.py` Phase 5 added (citizen01 test data); `--skip-citizen01` flag added; final summary updated with citizen01 verification instructions
- **Source**: agent (post-skill)
- **Plan**: 000170

### v19 -- 2026-06-24
- **Added**: `GET /forwardings/mine` endpoint (any authenticated role) returning `PublicForwardingResponse` list of forwardings containing at least one report authored by the current user; backed by new `find_by_author_id` DISTINCT JOIN repository method and `ListForwardingsForAuthor` use case
- **Added**: `useMyForwardings(enabled)` hook in `frontend/src/hooks/useForwardings.ts`; `api.getMyForwardings()` in `api.ts`
- **Added**: "Meus encaminhamentos" checkbox toggle in `PublicForwardingsPage` (visible when authenticated; `enabled=!!user` guard prevents unauthenticated 401)
- **Source**: agent (post-skill)
- **Plan**: 000169

### v18 -- 2026-06-24
- **Fixed**: Vote API URLs corrected in `frontend/src/api/votes.ts` (were `/votes` POST and `/votes/report/{id}/summary` GET; now `/reports/{id}/votes` POST/DELETE/GET and `/forwardings/{id}/votes` POST/DELETE/GET)
- **Added**: `GET /votes/reports/summary?ids=...` batch summary endpoint (max 200 IDs, optional auth)
- **Added**: `GET /reports/{id}/votes` and `GET /forwardings/{id}/votes` single-summary GET endpoints (optional auth)
- **Added**: `get_optional_user` dependency; `get_summaries_batch` on `IVoteRepository`/`SQLAlchemyVoteRepository`
- **Added**: `VoteButtons.readOnly` prop — shows counts without click handlers
- **Added**: "Meus relatos" nav link in Header (authenticated users); `WorkspacePage` applies author_id filter on mount via `?meus_relatos=1`
- **Added**: Inline `VoteButtons` per `TableView` row (batch fetch, readOnly for authors/anon, sort by upvotes)
- **Added**: `VoteButtons` in `ReportPopup` (map marker popup, per-open fetch)
- **Source**: agent (post-skill)
- **Plan**: plan-000164

### v17 -- 2026-06-24
- **Added**: `scripts/seed_all.py` — orchestrator that runs all four seed scripts (users → report_types → relatos → forwardings) in dependency order via subprocess; flags: `--count N` (default 100), `--full` (10 000), `--skip-forwardings`
- **Source**: agent (post-skill)
- **Plan**: plan-000161

### v16 -- 2026-06-24
- **Added**: Vote UX — `frontend/src/api/votes.ts` (castVote, retractVote, getVoteSummary), `VoteButtons.tsx` component; integrated into TableView relato dialog and PublicForwardingRow expanded card
- **Added**: Comment UX — `frontend/src/api/comments.ts`, `CommentSection.tsx` component; integrated into ForwardingRow (agent) and PublicForwardingRow (public)
- **Added**: Anonymous submission toggle on ReportFormPage; claim token dialog with clipboard copy; `localStorage['fala_gavea_anon_token']` persistence
- **Added**: Anonymous "Meus relatos" toggle in FilterPanel (shown when anon token exists and user is unauthenticated); `getMyAnonymousReports` in `api.ts`; `ANON_AUTHOR_SENTINEL` path in `useFilteredReports`
- **Changed**: `/report` route no longer always requires auth (RequireAuth removed; ReportFormPage shows login prompt when anonymous=false and not logged in)
- **Source**: agent (post-skill)
- **Plan**: roadmap-000151 (plans 000156, 000157, 000158)

### v15 -- 2026-06-23
- **Added**: `scripts/seed_forwardings.py` — seed script that authenticates as dev agent, queries pendente reports, draws 50% random sample grouped by report_type_id, and POSTs one Forwarding per sub-batch with institution/solution mapping
- **Source**: agent (post-skill)
- **Plan**: plan-000148

### v14 -- 2026-06-22
- **Added**: `IFilterParser` port + `ParseError` dataclass in `domain/repositories/filter_ports.py`
- **Added**: `LLMFilterParser` in `infrastructure/llm/llm_filter_parser.py` (wraps `ILLMClient`, 8s timeout, JSON extraction + one repair retry)
- **Added**: `ParseNLFilter` use case in `application/use_cases/nl/parse_nl_filter.py` (key allowlist + unknown-key warnings)
- **Added**: `POST /nl/filter` in `nl.py` router (20 req/min per-user via slowapi, auth required, 503 on unavailable, 429 on rate limit)
- **Added**: `NLFilterRequest`/`NLFilterResponse` Pydantic schemas in `presentation/schemas/nl_filter.py`
- **Added**: `postNLFilter(text, token)` in `frontend/src/api/nlFilter.ts` (maps 429→rate_limit, 503→unavailable)
- **Added**: `nlSuggestion`/`nlWarnings` state + `setNLSuggestion`/`applyNLSuggestion` actions to `workspaceStore`
- **Added**: Phase C NL assistant UI — Section 4 textarea (Enter/button submit), suggestion preview zone with chips and Aplicar/Descartar, pt-BR error messages; never auto-applies
- **Source**: agent (post-skill)
- **Plan**: 000140

### v13 -- 2026-06-21
- **Added**: `SavedFilter` domain entity + `ISavedFilterRepository` port; `SavedFilterModel` (SQLAlchemy, `DateTime(timezone=True)`, auto-created via `create_tables()`); `SQLAlchemySavedFilterRepository` (save/find_by_id/find_all_for_user/update/delete)
- **Added**: 5 use cases: `CreateSavedFilter`/`ListSavedFilters`/`GetSavedFilter`/`UpdateSavedFilter`/`DeleteSavedFilter` with BOLA enforcement (non-owned → 404); `SavedFilterNotFoundError` in `domain/exceptions.py`
- **Added**: CRUD router at `/saved-filters` (POST/GET/GET{id}/PATCH/DELETE); `SavedFilterResponse` schema with `deprecated_fields: []` for graceful schema migration
- **Added**: Phase B preset bar — Save popover (name input, auto-name fallback, Atualizar for loaded presets), Load dropdown (list + per-item trash delete), `*` dirty indicator; `workspaceStore` extended with `loadedPresetId`
- **Source**: agent (post-skill)
- **Plan**: 000139

### v12 -- 2026-06-21
- **Added**: Phase A UI overhaul — staged filter model (`filters` + `draftFilters` slices in `workspaceStore`), `applyFilters()`/`clearFilters()`/`discardDraft()`/`removeFilter()`/`setBbox()` actions, `isDirty()` derived selector
- **Added**: Four-section `FilterPanel` (`w-72`, collapsible), `ActiveFilterChips`, `DateRangePresets` (6 presets + custom), draft-loss guard via `useBlocker` + `beforeunload`
- **Changed**: `TableView` — column sort (`SortKey`), full-text Radix Dialog, pagination (PAGE_SIZE=50), score column (gated on `ranked_by==='similarity'`), density toggle
- **Changed**: `MapView` — "Filtrar nesta área" button replaces primary draw gesture; `setBbox` commits to both slices immediately
- **Changed**: SPA catch-all in `main.py` — `_API_PREFIXES` guard returns 404 JSON for known API prefixes; `getReportTypes()` and `getForwardings()` trailing-slash alignment in `api.ts`
- **Source**: agent (post-skill)
- **Plan**: 000137

### v11 -- 2026-06-21
- **Added**: `POST /reports/query` unified endpoint — multi-value filters (`report_type_ids[]`, `urgencies[]`, `statuses[]`), `bbox`, `since`/`until`, `text` ILIKE, optional `q` semantic rank; response envelope `{items, total, limit, offset, ranked_by}`; `ReportQueryRequest`/`ReportQueryItem`/`ReportQueryResponse` Pydantic schemas
- **Added**: `rank(query, ids) -> dict[str, float]` on `ISemanticSearchPort` (cosine similarity, no metadata mirroring); implemented in `ChromaSearchClient`
- **Added**: `find_page(filters, *, limit, offset, order, candidate_cap)` on `IReportRepository`; SQLAlchemy impl with count subquery + offset/limit
- **Added**: `QueryReports` use case (`application/use_cases/reports/query_reports.py`) — SQL filter → optional Chroma rank in-memory → paginate; `QueryPage` dataclass
- **Changed**: `ReportFilters` — single-value `report_type_id`/`urgency`/`status` replaced by plural lists; `text: str | None` added; legacy `/geojson` + `/keywords` wrap singletons transparently
- **Changed**: Frontend `useFilteredReports` — retargeted from dual GeoJSON+semantic calls to single `queryReports(POST /reports/query)`; `count = total` from envelope
- **Source**: agent (post-skill)
- **Plan**: plan-000132

### v1 -- 2026-06-19
- **Added**: Semantic AI foundation (Wave 0): deps chromadb/sentence-transformers/bertopic, domain ports IReportIndexer/ISemanticSearchPort/ITopicModelPort, EmbeddingProviderRegistry, ChromaSearchClient
- **Source**: agent (post-skill)
- **Plan**: plan-000089

### v2 -- 2026-06-19
- **Added**: Ingestion hook (Wave 0): IReportIndexer injected into CreateReport; get_report_indexer() singleton in dependencies.py; reports router updated; backfill_semantic.py script
- **Source**: agent (post-skill)
- **Plan**: plan-000090

### v3 -- 2026-06-19
- **Added**: Semantic search endpoints (Wave 1): public GET /reports/search and GET /reports/{id}/similar; use cases SearchReports + FindSimilarReports; get_semantic_search_port() dependency reusing the ChromaSearchClient singleton; ReportSearchResult schema (ReportResponse + score)
- **Source**: agent (post-skill)
- **Plan**: plan-000094

### v4 -- 2026-06-19
- **Added**: RAG chat NL assistant (Wave 2): ILLMClient domain port; infrastructure/llm/ package (OllamaAdapter, AnthropicClient, factory); AnswerWithRag use case with pt-BR system prompt and semantic context injection; POST /nl/chat (agent+admin); get_llm_client() dependency; anthropic>=0.50; FALA_GAVEA_LLM_PROVIDER / ANTHROPIC_API_KEY / FALA_GAVEA_ANTHROPIC_MODEL env vars
- **Source**: agent (post-skill)
- **Plan**: plan-000100

### v5 -- 2026-06-19
- **Changed**: §8 User Experience Patterns — `/` route refactored from MapPage (map-centric) to WorkspacePage (workspace grid pattern): Zustand workspaceStore, FilterPanel (live semantic query + aria-live count), ViewToggleBar (aria-pressed + focus mgmt), MapView (clustered markers, bbox draw), TableView (keyboard-accessible rows, Similares button), TopicsView (BERTopic, agent+admin, 503-resilient), SimilarsView (full-base, persistent caption), ChatView (RAG, cited_report_ids as focusable buttons). Cross-filter: in-memory intersection of geojson × semantic search ordered by score.
- **Added**: Journey Maps — JM-TB-003 implemented (exploration/analysis journey, plan-000104)
- **Source**: agent (post-skill)
- **Plan**: plan-000104


### v7 -- 2026-06-20
- **Added**: Admin bootstrap user (BootstrapAdminUser use case, env-var driven on startup), POST /admin/seed/topicos (BulkCreateReportTypes), DELETE /admin/seed/wipe (WipeDatabase use case; delete_all() on IReportIndexer/ChromaSearchClient)
- **Source**: agent (post-skill)
- **Plan**: plan-000109

### v6 -- 2026-06-20
- **Added**: POST /admin/seed/relatos (admin-only CSV bulk-insert endpoint): BulkCreateReports use case, BulkResult dataclass, find_by_name on IReportTypeRepository (case-insensitive), optional created_at param on Report.create(), SeedRelatosResponse schema, seed router wired under /admin/seed prefix
- **Source**: agent (post-skill)
- **Plan**: plan-000105

### v9 -- 2026-06-20
- **Added**: Batch indexing — `IReportIndexer.index_many` (ABC default-body fallback); `ChromaSearchClient.index_many` + vectorised `reindex_all`; `BulkCreateReports` chunked flush (CHUNK_SIZE=500) replacing per-row `index()` calls
- **Source**: agent (post-skill)
- **Plan**: plan-000120

### v10 -- 2026-06-21
- **Changed**: Embedding model default: `multilingual-e5-base` → `multilingual-e5-small`; `embed_model_topics` field removed from SemanticConfig; `EmbeddingProviderRegistry` no longer maps `topics` purpose
- **Changed**: Dockerfile forces CPU-only PyTorch via `UV_EXTRA_INDEX_URL`; pre-download target updated to `e5-small`
- **Removed**: `GET /reports/topics` endpoint; `BERTopicClient` dormant (installed, never instantiated); `_topic_model_instance` singleton removed from `dependencies.py`
- **Added**: `TfidfKeywordClient` (`infrastructure/topics/tfidf_keyword_client.py`): TF-IDF + K-means keyword extraction, no second model; `GET /reports/keywords` endpoint; `KeywordItem`/`KeywordListResponse` Pydantic schemas; `get_keyword_extractor()` dependency
- **Changed**: Frontend — `TopicItem`→`KeywordItem`, `useTopics`→`useKeywords`, ViewId `topics`→`keywords`, tab label `Tópicos`→`Palavras-chave`
- **Source**: agent (post-skill)
- **Plan**: plan-000124

### v8 -- 2026-06-20
- **Changed**: §9 Administrative Domain — enriched BulkCreateReports: per-row author from `user_id` (auto-create + dedup by synthetic e-mail, dev default password), auto-create unknown `topico` (guarded), Gávea-bbox random coords / `now` date / `media` urgency fallbacks; POST /admin/seed/relatos parses `user_id`+`urgency` columns (`id_cidadao` alias) and injects user_repo/password_service
- **Added**: Frontend — `api.seedRelatos(file)` + "Seed de Relatos" card (CSV upload + pt-BR rules) in AdminPage.tsx
- **Source**: agent (post-skill)
- **Plan**: plan-000113
