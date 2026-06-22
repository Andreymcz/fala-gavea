# Progress -- Plan 000140

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Codebase Patterns (populated by iteration 1)

- `ILLMClient` (in `semantic_ports.py`) only has `complete(system, messages)` — no `complete_with_timeout`. Adapted `LLMFilterParser` to use `complete()` directly.
- `ReportQueryRequest` fields confirmed: `report_type_ids`, `urgencies`, `statuses`, `since`, `until`, `bbox`, `text`, `q`, `limit`, `offset`. `_ALLOWED_KEYS` in `ParseNLFilter` matches spec exactly.
- `ParseError` is a `dataclass` that also inherits `Exception` — valid Python pattern.
- `OllamaClient.chat()` uses `httpx.Client(timeout=...)` — adding a `timeout` param to `chat()` and overriding `complete_with_timeout` in `OllamaAdapter` is clean and non-breaking.
- `test_static_spa.py::test_api_works_without_static_dir` was already failing before Steps 5–7 (pre-existing, unrelated to our changes).
- slowapi `_rate_limit_exceeded_handler` causes a pyright `arg-type` error vs FastAPI's `ExceptionHandler` union; suppressed with `# type: ignore[arg-type]`.

## Iteration Log

### 2026-06-21 — Steps 1–4 (commit d1def9b)

- Created `src/fala_gavea/domain/repositories/filter_ports.py` — `IFilterParser` ABC + `ParseError` dataclass.
- Created `src/fala_gavea/infrastructure/llm/llm_filter_parser.py` — `LLMFilterParser` with JSON extraction + one repair retry.
- Created `src/fala_gavea/application/use_cases/nl/__init__.py` (empty).
- Created `src/fala_gavea/application/use_cases/nl/parse_nl_filter.py` — `ParseNLFilter` use case.
- Created `src/fala_gavea/presentation/schemas/nl_filter.py` — `NLFilterRequest` / `NLFilterResponse` Pydantic schemas.
- Pyright: 0 errors, 0 warnings.
- Status: SUCCESS

### 2026-06-21 — Steps 5–7 (commit 3e46854)

- Added `complete_with_timeout(system, messages, timeout_s=120.0)` default impl to `ILLMClient` in `semantic_ports.py`.
- Updated `OllamaClient.chat()` to accept `timeout: float = 120.0` param.
- Overrode `complete_with_timeout` in `OllamaAdapter` to pass timeout to `OllamaClient.chat()`.
- Updated both `LLMFilterParser.parse()` calls to use `complete_with_timeout(..., timeout_s=8.0)`.
- Created `src/fala_gavea/presentation/api/routers/nl.py` — merged `/nl/chat` (from deleted `chat.py`) + new `/nl/filter` (rate-limited, 20/min via slowapi).
- Added `get_filter_parser()` singleton dependency to `dependencies.py`.
- Updated `main.py`: replaced `chat_router` with `nl_router`, added `app.state.limiter` and `RateLimitExceeded` exception handler.
- Added `slowapi>=0.1` to `pyproject.toml`; `uv sync` installed `slowapi==0.1.10`.
- Deleted `src/fala_gavea/presentation/api/routers/chat.py`.
- Pyright: 77 errors (all pre-existing; our 1 new error suppressed with `# type: ignore[arg-type]`).
- Tests: 162 passed (1 pre-existing failure in `test_static_spa.py` unrelated to our changes).
- Status: SUCCESS

### 2026-06-21 — Steps 8–9 (commit 6351057)

- Created `frontend/src/api/nlFilter.ts` — `postNLFilter(text, token)` calling `POST /nl/filter`; maps 429→`rate_limit`, 503→`unavailable` errors. Uses `WorkspaceFilters` as response body type (matches store shape; backend fields map directly).
- Updated `frontend/src/store/workspaceStore.ts` — added `nlSuggestion: Partial<WorkspaceFilters> | null` and `nlWarnings: string[]` state; added `setNLSuggestion(suggestion, warnings)` and `applyNLSuggestion(suggestion)` actions (non-destructive merge into draftFilters).
- Updated `frontend/src/features/workspace/FilterPanel.tsx` — replaced Section 4 disabled placeholder with functional NL assistant: textarea + send button (loading state), error messages in pt-BR (rate_limit / unavailable / generic), suggestion preview zone with chips and "Aplicar sugestão ao rascunho" / "Descartar" buttons. Uses `useAuth()` for token access.
- Build: `npm run build` succeeded (0 errors, 267 modules transformed).
- Status: SUCCESS
