# Research 000130 | REDESIGN-X | 2026-06-21 17:15 | Filter assistant: NL to query params, unified query API, saved filters

tags: filters, hybrid-search, llm-structured-output, api-design, saved-filters

source: user request -- NL filter assistant + richer query API + saved filters, layered on research-000129
spawned: plan-000132

## User brief (verbatim)

> filter assistant: natural language to query params. this will allow more complex queryes in relatos (wich will have to be supported by api) database. this could be a potent feature allowing the user to build complex queryes and visualize then. we could also build a feature to save logered user filters (save que query filter sent to api)

Clarifications captured in the Q&A:

> **Assistant output:** Structured editable filter (LLM returns a validated filter object that populates the FilterPanel; user sees/edits chips before applying).
>
> **Query ceiling:** "deep research a combination of multi-value, semantic text, with bbox. a busca pode ser uma api unica, manter /reports, os parametros da busca sao todos os disponiveis, incluindo a similaridade semantica (que hoje é busca semantica que será aplicada nos intervalos enviados também), o que a similaridade semantica pode fazer é ordenar os relatos de acordo com a similaridade, adicionar numero maximo de relatos ao filtro, com paginacao"
>
> **Saved filters:** Per-user private (all roles).
>
> **Scope:** Full feature, phased recommendation on top of research-000129.

## Agent interpretation

Three layered capabilities on top of the in-flight research-000129 staged-filter work (draft/Apply model + active-filter chips + temporal presets):

1. **Part A -- NL filter assistant.** User types natural language; a local LLM (Ollama `qwen3:8b`) translates it into a **structured, validated filter object** that populates the existing FilterPanel as **editable chips** in the *draft* state. It never auto-applies and never returns prose. Transparency + editability are the contract.
2. **Part B -- Unified richer query API on `/reports`.** Collapse today's two separate paths (`GET /reports/geojson` for structured filters, `GET /reports/search` for semantic) into **one query** where every parameter coexists: **multi-value** structured filters (urgency/type/status as lists), bbox, date range, an optional **semantic-similarity query that ranks the filtered set**, a **max-results cap**, and **pagination**. Semantic similarity becomes a *ranker applied within the structured-filter result set*, not a separate retrieval path.
3. **Part C -- Saved filters.** Per-user private named filters (all roles), persisted in SQLite -- save the exact query-filter object sent to the API and reload it later.

## Files

- `src/fala_gavea/domain/repositories/report_repository.py` -- `ReportFilters` (single-value today; extend to lists) + `find_all` (add pagination/sort/limit)
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` -- flat-AND query, no pagination/sort/full-text
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` -- `search`/`similar` take no `where`; metadata stores only `{lat, lon, urgency, report_type_id}` (no `status`, no `created_at`)
- `src/fala_gavea/presentation/api/routers/reports.py` -- `/geojson`, `/search`, `/{id}/similar`, `/keywords`
- `src/fala_gavea/presentation/schemas/report.py` -- `ReportFiltersQuery` (single-value)
- `src/fala_gavea/infrastructure/ollama/ollama_client.py` -- `chat()`; graceful 503 degradation
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` -- existing NL/RAG pattern to mirror for the parser use case
- `frontend/src/store/workspaceStore.ts` -- Zustand single `filters` object + `structuredFilters()`
- `frontend/src/lib/types.ts` -- `ReportFilters`, `WorkspaceFilters`
- `_output/research-logs/research-000129-refine-data-exploration-search-filters.md` -- in-flight staged draft/Apply model + chips that Part A populates; deprecation-sequencing constraint

---

## Findings

### F1 -- The hybrid query: keep SQL as the filter source of truth, Chroma as a ranker only

The core engineering question is how to combine SQL structured filtering with ChromaDB semantic ranking in one request. Industry guidance ([Dataquest](https://www.dataquest.io/blog/metadata-filtering-and-hybrid-search-for-vector-databases/), [Chroma Cookbook](https://cookbook.chromadb.dev/core/advanced/queries/)) frames it as *pre-filter vs post-filter by selectivity*: pre-filter for high selectivity (<10%), post-filter for low selectivity (>50%), hybrid in between. But at this project's scale (hundreds–low-thousands of reports, tight Railway RAM), the cleanest answer is neither of the exotic options:

- **Rejected -- push all filters into Chroma `where`:** would require **mirroring `status` and `created_at` into Chroma metadata** (currently absent) and keeping that dual-write consistent on every status change + re-index. Date-range `where` on a stored timestamp is awkward. It erodes the "all semantic calls through `infrastructure/`, SQL owns the data" boundary and adds an integrity failure mode.
- **Rejected -- constrain vector search to SQL-filtered candidate ids via `where {"id": {"$in": [...]}}`:** passing hundreds of ids into a `$in` negates index benefit and is fiddly.
- **Adopted -- SQL-filter-then-rank-in-memory:** SQL applies *all* structured filters (multi-value via `IN`, bbox, date range) and returns the candidate set. If a semantic `q` is present, embed it once, fetch the candidate embeddings from Chroma (`collection.get(ids=candidates, include=["embeddings"])`), score in memory, sort by similarity; otherwise sort by `created_at desc`. **SQL stays the single filter source of truth; Chroma is a pure ranker.** This also preserves research-000129's "one filter, many lenses" intent.

### F2 -- Pagination is correct only if the *entire filtered set* is ranked before slicing

You cannot page Chroma's `n_results` and also apply SQL filters: the top-n vectors may be mostly filtered out, so pages would be wrong/under-filled. The order is: **filter (SQL) -> cap at `max_results` -> rank the whole candidate set -> slice `[offset:offset+limit]`.** At this scale ranking a few hundred cached embeddings is trivial, and the `max_results` cap (e.g. 500) bounds memory on Railway. This makes pagination deterministic and stable across pages. The response should carry `ranked_by: "similarity" | "recency"` so the UI can label why rows are ordered as they are.

### F3 -- The editable-chips contract is the load-bearing security + reliability control for Part A

Because the LLM output is *rendered as editable draft filter params the user reviews before pressing Apply*, the worst case of prompt injection or hallucination degrades to "user sees a wrong chip and edits it" rather than "silent wrong query" -- the classic *"Looks fine to me"* failure. Reinforce this deliberately:

- (a) The LLM only ever populates the **draft**; it never auto-applies (reuse research-000129's Apply gesture).
- (b) Every emitted field is validated against the **same Pydantic schema the manual UI uses** -- enum membership for urgency/status/type, bbox/date bounds -- dropping invalid fields with a visible "não entendi X" note.
- (c) The prompt is constrained to emit **only a fixed JSON schema** via Ollama's `format` parameter (JSON-schema-guided decoding), so free-form prose and role/data leakage have no output channel.
- (d) The parsed filter still flows through the **same role-scoped query path** -- the LLM cannot widen visibility beyond what the user's role already grants.

For small local models this discipline is exactly what the literature recommends: SLMs match larger models on function-calling *when paired with explicit schemas + robust validators* ([SLM agentic survey](https://arxiv.org/pdf/2510.03847), [structured-output guide](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)). Implementation: Ollama `format=<json schema>` + Pydantic parse + **one repair retry** + graceful fallback (on 503/unparseable, return an empty draft with "assistente indisponível, preencha manualmente" -- never a silently wrong filter). The parser belongs in `infrastructure/` (extend `OllamaClient` or a sibling) returning a validated DTO; a use case orchestrates it -- mirroring the existing `AnswerWithRag` layering.

### F4 -- One additive `POST /reports/query`; deprecate the old endpoints only after the SPA migrates

A multi-value filter + semantic query + pagination is too complex for clean GET query params (repeated `urgency=`/`type=`, bbox encoding, no body). A **`POST /reports/query` with a Pydantic body** is more honest and self-documenting even though it is a read. But research-000129 is **actively reworking the SPA** against `/reports/geojson` and `/reports/search` -- removing them mid-flight would break in-progress work. So: introduce the new endpoint **additively**, migrate the SPA, then deprecate. Return a stable envelope:

```json
{ "items": [...], "total": 123, "limit": 50, "offset": 0, "ranked_by": "similarity" }
```

Note the map view needs GeoJSON and the table needs rows -- decide whether `items` is GeoJSON features or flat rows (recommend flat rows + lat/lon so both views derive from one payload, or a `format=geojson|rows` switch). The optional literal **full-text `text CONTAINS`** filter (cheap SQL `LIKE`) is a useful complement to semantic ranking and nearly free -- include it as one more field; semantic `q` ranks, `text` narrows.

> **REFINED (follow-up, 2026-06-21 17:55 UTC):** The sequencing in the paragraph above is **inverted by the designer's decision**. Rather than introducing the unified endpoint *additively after* research-000129's SPA migrates, **research-000130's `POST /reports/query` becomes the foundation, and research-000129 builds its front-end UI/UX on top of it.** Backend-first: ship the unified query API, then 129's FilterPanel (staged draft/Apply, chips, temporal presets) consumes it directly. The old `/geojson` + `/search` endpoints can still be removed once 129's frontend targets the new endpoint -- but 129 is no longer a *constraint that delays* the cutover; it is the *consumer* of the new contract. This also means 129 and 130 are co-designed: build them as one feature with a backend layer (130) under a frontend layer (129).

### F5 -- Saved filters: versioned JSON blob, per-user owned, validated on load

The filter shape will keep changing (multi-value, new fields, 129's presets), so a **normalized table would force a migration per field change**. Store a **versioned JSON blob**: `{ id, user_id, name, schema_version, filter_json, created_at }`, index `user_id`, FK to user. **Re-validate `filter_json` through the current Pydantic schema on load**, silently dropping/flagging fields that no longer exist (schema drift) -- never trust the blob as-is. Enforce ownership **server-side in the query** (`WHERE user_id = current_user.id`): a saved-filter id fetchable without the ownership check is a BOLA / horizontal-escalation hole. Reads/writes go through `dependencies.py` `get_current_user`. Report `text` can carry citizen PII, but saved filters store *query params*, not results, so the blob itself is low-sensitivity -- the risk is the ownership check, not the contents.

### F6 -- Phasing: B -> A -> C, and what to skip for a course project

`B` (unified query + pagination) is the foundation both `A` (NL populates a B-shaped draft) and `C` (saved filters reload a B-shaped body) depend on, so build it first. Layer on research-000129's draft/Apply chips rather than duplicating them. **Skip (gold-plating for this context):** candidate-id pre-filtering, Chroma metadata mirroring, HTTP cache headers, rate limiting, SDK-contract tests. **Do include:** per-user ownership checks, blob validate-on-load, the `max_results` cap, and at least one happy-path + one malformed-input test for the NL parser.

---

## Recommendations summary

| # | Recommendation | Priority |
|---|----------------|----------|
| R1 | **Unified `POST /reports/query`** (additive). Pydantic body: multi-value `report_type_ids[]`, `urgencies[]`, `statuses[]`, `bbox`, `since`/`until`, optional literal `text` (SQL LIKE), optional semantic `q` (ranker), `limit`, `offset`. Paginated envelope `{ items, total, limit, offset, ranked_by }`. Migrate the SPA off `/geojson` + `/search`, then deprecate them -- do **not** cut over mid-research-000129. | HIGH |
| R2 | **SQL-filter-then-rank-in-memory; SQL is the filter source of truth, Chroma is ranker-only.** Extend `ReportFilters` to lists (`IN` queries) + sort + `limit`/`offset`; add `max_results` cap before ranking; rank the *whole* filtered candidate set, then slice. Do **not** mirror `status`/`created_at` into Chroma. Add a candidate-set scoring path (`collection.get(ids, include=["embeddings"])` + in-memory cosine) so ranking is restricted to the filtered set. | HIGH |
| R3 | **NL->structured-filter assistant with the editable-draft contract.** Ollama `format` (JSON-schema-guided) + shared Pydantic validation + one repair retry + graceful 503/empty-draft fallback. LLM populates the **draft only** (never auto-apply); invalid/ambiguous fields dropped with a visible note. Parser lives in `infrastructure/`, orchestrated by a use case (mirror `AnswerWithRag`). This *is* the prompt-injection / hallucination mitigation. | HIGH |
| R4 | **Enforce role scoping + per-user ownership.** The unified query and NL path must not widen visibility beyond the user's role; saved-filter reads/writes filter by `user_id` server-side (BOLA prevention) via `dependencies.py`. NL filtering is safe to offer to all roles (it only produces filters), but confirm the policy explicitly. | HIGH |
| R5 | **Saved filters = versioned JSON blob.** One migration: `saved_filters(id, user_id FK+index, name, schema_version, filter_json, created_at)`. Validate `filter_json` through the current schema on load; drop/flag drifted fields rather than failing hard. CRUD endpoints scoped to the owner. | MEDIUM |
| R6 | **Phase B -> A -> C on top of research-000129; avoid gold-plating.** Skip candidate-id pre-filter, Chroma metadata mirroring, cache headers, rate limiting, SDK-contract tests. Include ownership checks, blob validate-on-load, `max_results` cap, and happy-path + malformed-input parser tests. | LOW |

**REFINED recommendations summary (follow-up, 2026-06-21 17:55 UTC)** -- supersedes the *sequencing* in R1/R6 only; all priorities and technical content above stand:

| # | Refinement | Priority |
|---|------------|----------|
| R1' | The unified `POST /reports/query` is the **foundation built first**, not an additive endpoint introduced after 129. research-000129 (FilterPanel staged draft/Apply, chips, temporal presets) is the **front-end consumer** layered on top of it. Co-design 129 + 130 as one feature (backend layer under frontend layer). Old `/geojson`+`/search` retired once 129 targets the new endpoint. | HIGH |
| R6' | Phasing becomes **B (unified query API) -> {129 frontend + A NL assistant} -> C (saved filters)**: B is the backend foundation, 129's UI/UX and the NL assistant both consume it, saved filters reload a B-shaped body. Capture the decisions formally via `/design` (create `product-design-as-intended.md` + D-NNN entries) before/with the full-feature plan. | HIGH |

**Considered & rejected:** (a) pushing all filters into Chroma `where` -- needs a status/created_at dual-write + re-index discipline that breaks SQL-as-source-of-truth; (b) constraining vector search via candidate-id `$in` -- negates the index, fiddly at hundreds of ids; (c) letting the NL assistant auto-apply filters for a snappier feel -- reintroduces the silent-wrong-query failure and a real injection surface, defeating the transparency goal.

---

## Q&A log

**Q1 (initial):** Build a "filter assistant" that turns natural language into query params, supported by a richer `/reports` query API (multi-value + semantic + bbox), with the ability to visualize/build complex queries and to save a logged-in user's filters.

**A1:** Six recommendations (R1-R6). Confirmed scope via the four clarifying questions: the assistant produces a **structured editable filter** (not prose); the query API becomes **one unified `/reports` query** combining multi-value structured filters + bbox + date range + an optional **semantic ranker** + max-results + pagination (semantic similarity orders the filtered set rather than being a separate path); saved filters are **per-user private for all roles**; and the research covers the **full feature with a phased B->A->C recommendation** layered on research-000129. The defining engineering decisions: keep **SQL as the filter source of truth and Chroma as a ranker-only** (filter-then-rank-in-memory, rank the whole filtered set before paginating); make the **editable-draft chips the security/reliability contract** for the NL parser (Ollama `format` JSON-schema + Pydantic validation + repair + graceful fallback, never auto-apply); expose the unified query as an **additive `POST /reports/query`** deprecating the old endpoints only after the SPA migrates; and store saved filters as a **versioned per-user JSON blob validated on load**.

**Q2 (follow-up):** How should research-000130 and research-000129 be sequenced?

**A2 (verbatim user):** "Research 129 can work on top of this Unified POST /reports/query and will focus on front end UI/UX. Edit this research, run design and plan full feature"

**A2 (resolution):** Sequencing inverted from the original F4/R1: **130's unified `POST /reports/query` is the backend foundation, built first; 129 is the front-end UI/UX layer that consumes it.** They are co-designed as one feature. Next actions: `/design` to formalize the design intent + D-NNN decisions, then `/plan` for the full feature (B + 129-frontend/A + C) with `source: research-000130`. See R1' / R6' above and the REFINED note under F4.

## Sources

- [Metadata Filtering and Hybrid Search for Vector Databases -- Dataquest](https://www.dataquest.io/blog/metadata-filtering-and-hybrid-search-for-vector-databases/)
- [Chroma Queries -- Chroma Cookbook](https://cookbook.chromadb.dev/core/advanced/queries/)
- [Hybrid Retrieval: Combining Metadata and Vector Search -- CodeSignal](https://codesignal.com/learn/courses/implementing-semantic-search-with-chromadb-1/lessons/hybrid-retrieval-combining-metadata-and-vector-search)
- [Small Language Models for Agentic Systems: A Survey -- arXiv](https://arxiv.org/pdf/2510.03847)
- [The guide to structured outputs and function calling with LLMs -- Agenta](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
- [SLOT: Structuring the Output of Large Language Models -- arXiv](https://arxiv.org/pdf/2505.04016)
