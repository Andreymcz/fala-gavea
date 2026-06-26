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
