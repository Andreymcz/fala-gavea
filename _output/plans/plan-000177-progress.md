# Progress -- Plan 000177

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

- **Lazy-singleton dependency pattern** (`src/fala_gavea/presentation/api/dependencies.py:122-169`): use a module-global sentinel `_X_INIT_FAILED = object()` + `threading.Lock()`; return `None` on init failure so the server stays up. Mirror this for `get_doc_search_port()` and `get_embedding_model()`.
- **ChromaDB client conventions** (`src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`): `chromadb.PersistentClient(path=config.vectorstore_path)`; e5 prefixes `passage: {text}` (index) and `query: {text}` (search); score = `1.0 / (1.0 + distance)`. Documents stored IN chroma.
- **Router 503 contract** (`src/fala_gavea/presentation/api/routers/nl.py`): raise `HTTPException(503, detail=...)` when LLM/search port is `None`; per-IP slowapi `limiter` (`@limiter.limit("20/minute")`, needs `request: Request` param).
- **ILLMClient** (`domain/repositories/semantic_ports.py`): `complete(system: str, messages: list[dict[str,str]]) -> str`.
- Run tests with `uv run pytest`; lint `uv run ruff check src/ tests/`; types `uv run pyright src/`. Frontend: `cd frontend && npm run build` / `npm run test`.

## Iteration Log

### Step 1 — Domain ports (DocChunk, IDocSearchPort, IDocIndexer) — SUCCESS

- Created `src/fala_gavea/domain/repositories/doc_ports.py` (doc bounded context, fully separate from `semantic_ports.py`).
- Exports: `DocChunk`, `DocSearchHit`, `IDocSearchPort`, `IDocIndexer`.
- **`DocChunk` constructor signature (field order — positional or keyword)**: `DocChunk(chunk_id: str, text: str, source_path: str, doc_type: str, section_title: str, chunk_index: int, role_visibility: str)`. `chunk_id` convention is `f"{source_path}#{chunk_index}"`; `section_title` is `""` when no heading.
- `DocSearchHit(chunk: DocChunk, score: float)` — score in [0,1].
- `IDocSearchPort.search(self, query: str, *, roles: list[str], n: int = 5) -> list[DocSearchHit]` — `roles` is keyword-only; returns chunk text directly (no SQL hydration). `IDocSearchPort.ready() -> bool`.
- `IDocIndexer.reindex_all(self, chunks: list[DocChunk]) -> None` (full replace) and `count() -> int`.
- Tests in `tests/domain/test_doc_ports.py`: 5 passed (field types for both dataclasses, empty section_title, ABCs raise TypeError on direct instantiation). Verify command exits 0. Ruff clean.
- Gotcha: `doc_type` line in source exceeds ruff's default line length only as a comment — ruff E501 ignores it here (passed clean); keep the long enumerated comment as a trailing comment, not wrapped, to avoid breaking the field declaration.

### Step 2 — Markdown chunker + role-visibility classifier + corpus walker — SUCCESS

- Created `src/fala_gavea/infrastructure/docs/__init__.py` (empty) and `src/fala_gavea/infrastructure/docs/markdown_chunker.py` (pure functions, no Chroma/embedding deps).
- Tests `tests/infrastructure/test_markdown_chunker.py`: 23 passed. Ruff clean.
- **Public signatures:**
  - `classify_visibility(source_path: str) -> tuple[str, str]` — default-deny; returns `(doc_type, role_visibility)`.
  - `is_excluded(source_path: str) -> bool`.
  - `chunk_markdown(text: str, *, source_path: str, max_chars: int = 3200, overlap: int = 200) -> list[DocChunk]`.
  - `walk_corpus(roots: list[str], repo_root: str) -> list[DocChunk]`.
- `_DEFAULT_ROOTS = ["_output/plans", "_output/research-logs", "_output/reflections", "_output/communication", "product-design/project"]`.
- `_SECRET_PATTERNS` = `(re.compile(r"sk-[A-Za-z0-9]{20,}"), re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"))`. Verified: bare env-var names (`ANTHROPIC_API_KEY`, `FALA_GAVEA_OLLAMA_URL`) with no value assignment are RETAINED; value-shaped secrets (`sk-...`, `api_key = "..."`) drop the whole sub-chunk.
- **Gotcha for Step 7 (reuses `walk_corpus`)**: `walk_corpus` uses `Path.rglob("*.md")` and skips non-existent roots silently (no error). `source_path` is normalized to forward slashes via `.as_posix()`. `chunk_index` is contiguous (0-based) across the *whole document* after secret/empty drops — i.e. dropped chunks do NOT leave gaps because the index counter only increments on appended chunks. `classify_visibility` matches on forward-slash paths only; callers must pass repo-relative paths (walk_corpus already does). Empty-body sections (heading with no text) are skipped, so a heading-only file yields zero chunks.

### Step 3 — ChromaDocSearchClient (own collection, role-filtered query) — SUCCESS

- Created `src/fala_gavea/infrastructure/chromadb/chroma_doc_search_client.py` implementing `IDocIndexer` + `IDocSearchPort`.
- **Constructor signature**: `ChromaDocSearchClient(config: SemanticConfig, model: SentenceTransformer)` — the model is INJECTED (not loaded inside the class) so Step 4 can share one model instance between the reports client and this one.
- **`getattr` note for Step 4**: collection name read defensively via `getattr(config, "selfdocs_collection", "falagavea_selfdocs")` (module const `_DEFAULT_COLLECTION_NAME`), stored as `self._collection_name`. Step 4 must ADD a real `selfdocs_collection` field to `SemanticConfig` (in `infrastructure/embeddings/registry.py`); the getattr keeps Step 3 independently testable and forward-compatible — no change needed here once the field lands.
- **`search` -> `DocSearchHit`**: encodes `query: {query}`, calls `collection.query(query_embeddings=[emb], n_results=n, where={"role_visibility": {"$in": roles}})`, then zips `ids[0]`/`documents[0]`/`metadatas[0]`/`distances[0]` into a `DocChunk` (rebuilt from metadata) wrapped in `DocSearchHit(chunk, score)` with `score = 1.0/(1.0+dist)`. The `text` comes from `documents[0]` (stored in Chroma), the rest of the chunk fields from metadata.
- **Fail-closed `where` filter — PASSED**: `test_search_public_role_excludes_internal` indexes a `public` + an `internal` chunk, searches `roles=["public"]`, and asserts exactly 1 hit AND no hit has `role_visibility == "internal"`. Chroma applies the `where={"role_visibility": {"$in": roles}}` clause server-side (rows excluded before ranking), so the filter holds regardless of the fake encoder's ranking. `roles=["public","internal"]` returns both. The `where` clause is always passed — never built conditionally.
- **Empty handling**: `search` returns `[]` early when `collection.count() == 0`, and also guards `if not ids: return []` after the query. `reindex_all([])` deletes+recreates the collection then returns (stays empty). `ready()` = `count() > 0`.
- **GOTCHA — ChromaDB metadata typing**: `chunk_index` MUST be a plain Python `int` in the metadata dict — wrapped as `int(c.chunk_index)` on write and `int(meta["chunk_index"])` on read. Chroma rejects numpy ints / non-primitive metadata values. All metadata values are str/int primitives only.
- **GOTCHA — test fake encoder**: `reindex_all` batch-encodes via `model.encode([...], batch_size=64, show_progress_bar=False)`; `search` single-encodes `model.encode(str)`. The fake/stub encoder in tests must accept `batch_size`/`show_progress_bar` kwargs AND return a 1D vector for `str` input but a 2D matrix for `list[str]` input (mirroring SentenceTransformer) — a fixed-dim (16) char-bucket hash works and needs no model download.
- Tests `tests/infrastructure/test_chroma_doc_search_client.py`: 7 passed (real ephemeral PersistentClient in `tmp_path`, `_StubConfig` dataclass with `vectorstore_path`+`selfdocs_collection="test_selfdocs"`). Ruff clean. Committed (explicit staging, no `git add -A`).

### Step 4 — SemanticConfig selfdocs fields + get_embedding_model + get_doc_search_port — SUCCESS

- **`SemanticConfig` new fields** (`infrastructure/embeddings/registry.py`): `selfdocs_collection: str` (env `FALA_GAVEA_SELFDOCS_COLLECTION`, default `"falagavea_selfdocs"`); `selfdocs_corpus_roots: list[str]` (env `FALA_GAVEA_SELFDOCS_ROOTS` comma-separated; empty/unset -> `_DEFAULT_ROOTS`). The Step-3 `getattr(config, "selfdocs_collection", ...)` in `chroma_doc_search_client.py` now resolves to the real field with no change needed there.
- **`_DEFAULT_ROOTS` location**: defined LOCALLY in `registry.py` (same 5 paths as `infrastructure/docs/markdown_chunker.py`). Deliberately duplicated to avoid embeddings/->docs/ import coupling; **Rule-of-Three NOT triggered** (only 2 copies). If a 3rd consumer appears, extract to a shared module. `_split_roots(s: str) -> list[str]` helper splits comma-separated, trims, drops empties.
- **`ChromaSearchClient.__init__(config, model: SentenceTransformer | None = None)`** — backward-compatible: when `model is None` it constructs its own `SentenceTransformer(config.embed_model_search)` (scripts/existing tests still work); when injected, reuses the shared instance. Existing `test_chroma_search_client.py` (constructs `ChromaSearchClient(config)`, patches `SentenceTransformer`) stays green.
- **New `dependencies.py` accessors**:
  - `get_embedding_model() -> SentenceTransformer` — thread-safe lazy singleton (globals `_embedding_model_instance` + `_embedding_model_lock`); imports `SentenceTransformer` + `SemanticConfig` lazily inside the fn; loads `SemanticConfig().embed_model_search` once.
  - `get_doc_search_port() -> IDocSearchPort | None` — mirrors `get_report_indexer`: sentinel `_DOC_INIT_FAILED = object()` + `_doc_search_lock`; builds `ChromaDocSearchClient(SemanticConfig(), get_embedding_model())`; returns `None` (sticky) on any Exception with a logged warning.
  - `get_report_indexer()` now passes `model=get_embedding_model()` so reports + docs share ONE model instance. Degraded path: doc search obtains the model via `get_embedding_model()` directly, so it works even if reports Chroma init failed.
- **Model-injection / no private reach**: NO production code reads `ChromaSearchClient._model` (grep over `src/` confirmed all `._model` are intra-class). One unit test (`test_chroma_search_client_uses_injected_model`) asserts `client._model is injected` — that is a white-box unit assertion, not production coupling.
- **GLOBAL-RESET TESTING GOTCHA**: `get_embedding_model()` and `get_doc_search_port()` cache into module globals `_embedding_model_instance` / `_doc_search_instance` (and the latter can latch the `_DOC_INIT_FAILED` sentinel). Tests MUST reset these before+after each test or state leaks (a stale cached object or sticky failure flips unrelated tests). `tests/unit/presentation/test_dependencies_doc_search.py` uses an `autouse` fixture that sets both globals back to `None` around every test. Patch the SUCCESS path via `patch.object(deps, "get_embedding_model", ...)` and `patch(".../ChromaDocSearchClient")`; for `get_embedding_model` itself patch `sentence_transformers.SentenceTransformer`.
- **Tests**: `tests/unit/infrastructure/test_semantic_config.py` (7) + `tests/unit/presentation/test_dependencies_doc_search.py` (5+ incl. backward-compat + injected-model + None-on-failure). Targeted `-k "semantic_config or dependencies or chroma_search"` = 17 passed. Verify cmd prints `falagavea_selfdocs 5`. Ruff clean on all 5 files. **Full `uv run pytest -q` = 289 passed, 0 regressions** (existing reports-client tests green). Committed with explicit staging (no `git add -A`).

### Step 5 — AnswerHelpWithRag use case (hardened prompt, citations) — SUCCESS

- Created `src/fala_gavea/application/use_cases/help/__init__.py` (empty) and `src/fala_gavea/application/use_cases/help/answer_help_with_rag.py`.
- **Dataclass shapes (field order — Step 6 maps these to Pydantic):**
  - `CitedDoc(source_path: str, section_title: str, score: float)`
  - `HelpAnswer(response: str, cited_docs: list[CitedDoc])`
- **`AnswerHelpWithRag.__init__(self, search_port: IDocSearchPort, llm_client: ILLMClient, top_k: int = 5)`**; `execute(self, message: str, *, roles: list[str]) -> HelpAnswer`. `roles` is keyword-only and forwarded VERBATIM to `search_port.search(message, roles=roles, n=top_k)`.
- **Exact not-found message string** (returned when `search` yields 0 hits; LLM is NOT called in this path): `"Não encontrei essa informação na documentação da plataforma Fala-Gávea."` (module const `_NOT_FOUND_PT_BR`).
- **Grounding/hardening**: hits present → system prompt = `f"{_SYSTEM_PT_BR}\n\n<DOCUMENTOS>\n{block}\n</DOCUMENTOS>"` where each line is `f"[{hit.chunk.source_path}#{hit.chunk.section_title}] {hit.chunk.text}"` joined by `\n`. `_SYSTEM_PT_BR` declares the chunks as untrusted DADOS (anti prompt-injection). LLM called as `complete(system, [{"role":"user","content":message}])`; `cited_docs` = one `CitedDoc(source_path, section_title, score)` per hit, in hit order.
- **Tests** `tests/application/test_answer_help_with_rag.py`: 3 passed — (a) hits populate cited_docs + system contains each chunk text and `<DOCUMENTOS>` delimiter + user message forwarded; (b) no hits → `cited_docs==[]`, response is the not-found string, fake LLM `call_count==0`; (c) roles/query/n forwarded verbatim to the fake search port. Fakes subclass `IDocSearchPort`/`ILLMClient` and record args. Ruff clean on all 3 files. `uv run pytest -k "answer_help"` = 3 passed, 289 deselected. Committed with explicit staging (no `git add -A`).
