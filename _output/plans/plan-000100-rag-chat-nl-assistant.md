# DONE | 2026-06-19 18:58 UTC | Plan 000100 | fala-gavea/rag-chat | 2026-06-19 | RAG chat NL assistant backend | Review: light
plan_format_version: 1

## Context

Roadmap 000088 Wave 2 item 6 — `rag-chat`.

The existing `POST /chat` endpoint (`presentation/api/routers/chat.py`) is a simple Ollama
pass-through: it accepts raw message arrays and calls `OllamaClient` directly, violating
CONVENTION_1 (LLM access must go through `infrastructure/` via domain ports). It has no RAG
retrieval, no cited reports, and no role restriction.

This plan upgrades the chat endpoint to a proper RAG assistant:

1. Adds `ILLMClient` domain port.
2. Creates `infrastructure/llm/` with `OllamaAdapter`, `AnthropicClient`, and `factory.py`.
3. Creates `AnswerWithRag` use case that retrieves top-k reports from `ISemanticSearchPort`,
   builds a pt-BR system prompt, calls `ILLMClient`, and returns `{response, cited_report_ids}`.
4. Replaces the existing thin chat router with one that wires the use case, restricts to
   `agent`/`admin`, and returns the new schema.
5. Adds `anthropic` SDK to `pyproject.toml`.
6. Unit-tests `AnswerWithRag` and the router with mocked ports (no network).

**Privacy note (D-F):** `FALA_GAVEA_LLM_PROVIDER=ollama` (default) keeps report text local.
`anthropic` sends retrieved report snippets to Anthropic's API. Default preserves local-only.

---

## Dependencies

- plan-000094 (semantic-search + similar-reports backends) — `ISemanticSearchPort` and
  `ChromaSearchClient` must already be wired. Both are ✓ done per roadmap-000088.

---

## Affected files

| File | Action |
|------|--------|
| `src/fala_gavea/domain/repositories/semantic_ports.py` | add `ILLMClient` ABC |
| `src/fala_gavea/infrastructure/llm/__init__.py` | new (empty) |
| `src/fala_gavea/infrastructure/llm/ollama_adapter.py` | new — wraps `OllamaClient`, implements `ILLMClient` |
| `src/fala_gavea/infrastructure/llm/anthropic_client.py` | new — Anthropic SDK, implements `ILLMClient` |
| `src/fala_gavea/infrastructure/llm/factory.py` | new — resolves `ILLMClient` by `FALA_GAVEA_LLM_PROVIDER` |
| `src/fala_gavea/application/use_cases/chat/__init__.py` | new (empty) |
| `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` | new — `AnswerWithRag` use case |
| `src/fala_gavea/presentation/schemas/chat.py` | new — `ChatRequest`, `ChatResponse` |
| `src/fala_gavea/presentation/api/routers/chat.py` | replace — wires use case, adds role guard |
| `src/fala_gavea/presentation/api/dependencies.py` | add `get_llm_client()` dependency |
| `pyproject.toml` | add `anthropic>=0.50` dependency |
| `tests/unit/test_answer_with_rag.py` | new — unit tests with mocked ports |
| `tests/integration/test_chat_rag.py` | new — integration tests via TestClient |

---

## Steps

### Step 1 — Add `ILLMClient` domain port

**File:** `src/fala_gavea/domain/repositories/semantic_ports.py`

Append after `ITopicModelPort`:

```python
class ILLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, messages: list[dict[str, str]]) -> str: ...
```

`system` is a system-prompt string. `messages` is the conversation history
`[{"role": "user"|"assistant", "content": "..."}]`. Returns the assistant reply as a string.

---

### Step 2 — `infrastructure/llm/` — OllamaAdapter

**File:** `src/fala_gavea/infrastructure/llm/ollama_adapter.py`

Thin adapter that wraps the existing `OllamaClient` and implements `ILLMClient`:

```python
from __future__ import annotations
from fala_gavea.domain.repositories.semantic_ports import ILLMClient
from fala_gavea.infrastructure.ollama.ollama_client import OllamaClient


class OllamaAdapter(ILLMClient):
    def __init__(self) -> None:
        self._client = OllamaClient()

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        return self._client.chat(full_messages)
```

`OllamaClient.chat()` already speaks the Ollama `/api/chat` format; prepending a system message
is enough to satisfy the port contract.

---

### Step 3 — `infrastructure/llm/` — AnthropicClient

**File:** `src/fala_gavea/infrastructure/llm/anthropic_client.py`

```python
from __future__ import annotations

import os
from anthropic import Anthropic
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicClient(ILLMClient):
    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set")
        self._client = Anthropic(api_key=api_key)
        self._model = os.environ.get("FALA_GAVEA_ANTHROPIC_MODEL", _DEFAULT_MODEL)

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
```

`ANTHROPIC_API_KEY` is read from env only — never hardcoded.

---

### Step 4 — `infrastructure/llm/factory.py`

```python
from __future__ import annotations

import logging
import os
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_log = logging.getLogger(__name__)


def create_llm_client() -> ILLMClient:
    """Resolve ILLMClient via FALA_GAVEA_LLM_PROVIDER (ollama | anthropic)."""
    provider = os.environ.get("FALA_GAVEA_LLM_PROVIDER", "ollama").strip().lower()
    if provider == "anthropic":
        from fala_gavea.infrastructure.llm.anthropic_client import AnthropicClient
        return AnthropicClient()
    # default: ollama
    if provider != "ollama":
        _log.warning("Unknown LLM provider %r — falling back to ollama", provider)
    from fala_gavea.infrastructure.llm.ollama_adapter import OllamaAdapter
    return OllamaAdapter()
```

---

### Step 5 — `AnswerWithRag` use case

**File:** `src/fala_gavea/application/use_cases/chat/answer_with_rag.py`

```python
from __future__ import annotations

from dataclasses import dataclass

from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort

_SYSTEM_PT_BR = (
    "Você é um assistente de exploração de demandas urbanas da Gávea. "
    "Responda sempre em português do Brasil. "
    "Use apenas as informações dos relatos fornecidos como contexto. "
    "Se não houver contexto suficiente, diga que não encontrou relatos relevantes. "
    "Não invente informações."
)

_TOP_K = 5


@dataclass
class RagAnswer:
    response: str
    cited_report_ids: list[str]


class AnswerWithRag:
    def __init__(
        self,
        search_port: ISemanticSearchPort,
        report_repo: IReportRepository,
        llm_client: ILLMClient,
        top_k: int = _TOP_K,
    ) -> None:
        self._search = search_port
        self._repo = report_repo
        self._llm = llm_client
        self._top_k = top_k

    def execute(self, message: str) -> RagAnswer:
        hits = self._search.search(message, n=self._top_k)
        cited_ids = [rid for rid, _score in hits]

        context_parts: list[str] = []
        for rid, score in hits:
            report = self._repo.find_by_id(rid)
            if report is not None:
                context_parts.append(
                    f"[{rid}] (score={score:.2f}) {report.text}"
                )

        if context_parts:
            context_block = "\n".join(context_parts)
            system = (
                f"{_SYSTEM_PT_BR}\n\n"
                f"Relatos relevantes encontrados:\n{context_block}"
            )
        else:
            system = _SYSTEM_PT_BR

        messages = [{"role": "user", "content": message}]
        reply = self._llm.complete(system, messages)
        return RagAnswer(response=reply, cited_report_ids=cited_ids)
```

**Key decisions:**
- Uses `ISemanticSearchPort.search()` (already wired via `ChromaSearchClient`).
- Hydrates report text via `IReportRepository.find_by_id()` to build context.
- System prompt is pt-BR, instructs model to cite only provided context.
- Falls back gracefully when semantic search is cold (empty collection).

---

### Step 6 — Presentation schema

**File:** `src/fala_gavea/presentation/schemas/chat.py`

```python
from __future__ import annotations
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # reserved for future multi-turn; ignored for now


class ChatResponse(BaseModel):
    response: str
    cited_report_ids: list[str]
```

---

### Step 7 — Refactor `chat.py` router

**File:** `src/fala_gavea/presentation/api/routers/chat.py`

Replace the existing thin pass-through with the RAG-backed version:

```python
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort
from fala_gavea.presentation.api.dependencies import (
    get_llm_client,
    get_report_repo,
    get_semantic_search_port,
    require_any_role,
)
from fala_gavea.presentation.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def nl_chat(
    body: ChatRequest,
    _current_user: User = Depends(require_any_role("agent", "admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
    llm_client: ILLMClient | None = Depends(get_llm_client),
) -> ChatResponse:
    if llm_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider is not configured.",
        )
    if search_port is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is not available.",
        )
    use_case = AnswerWithRag(search_port, report_repo, llm_client)
    result = use_case.execute(body.message)
    return ChatResponse(response=result.response, cited_report_ids=result.cited_report_ids)
```

**Breaking change note:** the request/response schema changes:
- Old: `{messages: list[dict]}` → `{reply: str}`
- New: `{message: str, session_id?: str}` → `{response: str, cited_report_ids: list[str]}`

The old schema was a thin pass-through with no documented consumers; the frontend chat panel
(Wave 3 item 8, `plan-TBD`) will be built against the new schema.

---

### Step 8 — Add `get_llm_client()` to `dependencies.py`

Append to `src/fala_gavea/presentation/api/dependencies.py`:

```python
_llm_client_instance: "ILLMClient | None" = None


def get_llm_client() -> "ILLMClient | None":
    global _llm_client_instance
    if _llm_client_instance is None:
        try:
            from fala_gavea.infrastructure.llm.factory import create_llm_client
            _llm_client_instance = create_llm_client()
        except Exception as exc:
            _log.warning("LLM client unavailable: %s", exc)
    return _llm_client_instance
```

Also add `ILLMClient` to the import from `semantic_ports` at the top of the file.

---

### Step 9 — Add `anthropic` SDK to `pyproject.toml`

```bash
uv add "anthropic>=0.50"
```

This adds the official Anthropic Python SDK. It is only instantiated when
`FALA_GAVEA_LLM_PROVIDER=anthropic` is set.

---

### Step 10 — Unit tests

**File:** `tests/unit/test_answer_with_rag.py`

Test `AnswerWithRag` with fully mocked ports — no network, no model download.

Scenarios:
1. **Happy path with hits**: search returns 2 report ids → `AnswerWithRag.execute()` hydrates
   both, calls `ILLMClient.complete()` with a system prompt containing report texts, returns
   `RagAnswer` with correct `cited_report_ids` and `response`.
2. **Empty semantic index**: search returns `[]` → use case calls LLM with bare system prompt
   (no context block), returns empty `cited_report_ids`.
3. **Report not found in repo**: search returns an id but `find_by_id` returns `None` →
   context block is empty for that id, LLM still called, no crash.
4. **LLM raises**: `ILLMClient.complete()` raises `RuntimeError` → exception propagates
   (router layer handles 503).

---

### Step 11 — Integration tests

**File:** `tests/integration/test_chat_rag.py`

Use `TestClient` + `app.dependency_overrides` to inject stub `ISemanticSearchPort`,
`IReportRepository`, and `ILLMClient`.

Scenarios:
1. **agent role → 200**: authenticated agent sends `{"message": "buracos na rua"}` → receives
   `{"response": "...", "cited_report_ids": [...]}`.
2. **citizen role → 403**: citizen token rejected.
3. **unauthenticated → 401**.
4. **LLM unavailable (get_llm_client returns None) → 503**.
5. **Semantic search unavailable (get_semantic_search_port returns None) → 503**.

---

## Execution order

Steps 1–9 can be done in one pass (no inter-step blockers). Steps 10–11 follow.

```
Step 1  → semantic_ports.py (add ILLMClient)
Step 2  → infrastructure/llm/ollama_adapter.py
Step 3  → infrastructure/llm/anthropic_client.py
Step 4  → infrastructure/llm/factory.py
Step 5  → application/use_cases/chat/answer_with_rag.py
Step 6  → presentation/schemas/chat.py
Step 7  → presentation/api/routers/chat.py  (replace)
Step 8  → presentation/api/dependencies.py  (append)
Step 9  → pyproject.toml  (uv add anthropic)
Step 10 → tests/unit/test_answer_with_rag.py
Step 11 → tests/integration/test_chat_rag.py
```

---

## Verification

```bash
uv run pytest tests/unit/test_answer_with_rag.py tests/integration/test_chat_rag.py -v
uv run ruff check src/ tests/
uv run pyright src/
```

All tests must pass with no network or model downloads.

---

## Completion Summary — 2026-06-19

**Steps completed:** 11/11 | **Iterations used:** 2 subagents

**Key outcomes:**
- `ILLMClient` ABC added to `semantic_ports.py`
- `infrastructure/llm/` package: `OllamaAdapter`, `AnthropicClient`, `factory.py`
- `AnswerWithRag` use case with pt-BR system prompt and semantic context injection
- `presentation/schemas/chat.py` with `ChatRequest`/`ChatResponse`
- `routers/chat.py` refactored — RAG-backed, agent/admin only, 503 on missing deps
- `get_llm_client()` dependency added to `dependencies.py`
- `anthropic>=0.50` (resolved 0.111.0) added via uv

**Test results:** 9/9 pass (4 unit, 5 integration). Lint clean. No new pyright errors.

**Notable finding:** Chat router is mounted under `/nl` prefix → full path is `/nl/chat`.
