# Progress -- Plan 000100

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### 2026-06-19 — Steps 1-11 completed

**Gotchas:**
- `OllamaClient.chat()` signature is `chat(messages: list[dict[str, Any]], stream: bool = False) -> str` — fully compatible with the adapter approach.
- `Report.text` is the correct field name for the report body text.
- `require_any_role` already existed in `dependencies.py` — no changes needed there.
- Pre-existing E501 (line-too-long) violations in unrelated files; none introduced by this plan.
- The old `chat.py` router had inline `ChatRequest`/`ChatResponse` Pydantic models — moved to `presentation/schemas/chat.py`.
- `get_llm_client` added to dependencies and `ILLMClient` added to the semantic_ports import in dependencies.py.

**Files created:**
- `src/fala_gavea/domain/repositories/semantic_ports.py` — appended `ILLMClient`
- `src/fala_gavea/infrastructure/llm/__init__.py`
- `src/fala_gavea/infrastructure/llm/ollama_adapter.py`
- `src/fala_gavea/infrastructure/llm/anthropic_client.py`
- `src/fala_gavea/infrastructure/llm/factory.py`
- `src/fala_gavea/application/use_cases/chat/__init__.py`
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py`
- `src/fala_gavea/presentation/schemas/chat.py`

**Files modified:**
- `src/fala_gavea/presentation/api/routers/chat.py` — full refactor to RAG-backed endpoint
- `src/fala_gavea/presentation/api/dependencies.py` — added `get_llm_client`, `ILLMClient` import
- `pyproject.toml` / `uv.lock` — added `anthropic>=0.50` (resolved to 0.111.0)

### 2026-06-19 — Steps 10-11 completed (this iteration)

**Result:** 9/9 tests pass.

**Gotchas:**
- Chat router is mounted at `/nl` prefix in `main.py` (`prefix="/nl"`), so the endpoint is `/nl/chat` — not `/chat`.
- Integration tests reuse the same DB-patching pattern from `tests/conftest.py` (swap `_db_mod.engine` + `_db_mod.SessionLocal` before importing models).
- `dependency_overrides` must be cleared after each test to avoid cross-test contamination.

**Files created:**
- `tests/unit/application/test_answer_with_rag.py` — 4 unit tests for `AnswerWithRag` use case (fully mocked)
- `tests/integration/api/test_chat_rag.py` — 5 integration tests for `POST /nl/chat` router via `TestClient`
