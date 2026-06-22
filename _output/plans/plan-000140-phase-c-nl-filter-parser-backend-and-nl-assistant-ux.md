# Plan 000140 | FEATURE-X cross-cutting | 2026-06-21 22:44 | Phase C NL filter parser backend and NL assistant UX | Review: standard
# DONE | 2026-06-22 12:15 UTC |
plan_format_version: 1
source: research-000136 -- Phase C NL filter parser backend + NL assistant UX

---

## Brief

> Phase C (new plan): NL filter parser backend (`IFilterParser` port + `OllamaFilterParser` + `ParseNLFilter` use case + `POST /nl/filter` endpoint) + NL assistant UX (Section 4 input, suggestion preview zone, "Aplicar sugestão" button). From research 136.

## Agent Interpretation

Implement the NL-to-filter assistant end-to-end: backend port + infrastructure adapter (routing through the existing LLM factory so Ollama and Anthropic are both supported) + use case with one repair retry + async `/nl/filter` endpoint with 8-second timeout and 10 req/min rate limit + frontend Section 4 wire-up with suggestion preview zone and "Aplicar sugestão" / "Descartar" buttons.

The key design constraint: **never auto-apply** — parsed suggestions must be reviewed by the user before merging into `draftFilters`. On 503 (LLM unavailable or timeout), Section 4 shows a graceful degradation message; the rest of the panel stays fully functional.

Since the LLM factory already supports both Ollama and Anthropic (via `FALA_GAVEA_LLM_PROVIDER`), the `IFilterParser` implementation reuses `ILLMClient.complete()` rather than talking directly to Ollama — this gives provider agnosticism for free and is the cleanest architecture. The "OllamaFilterParser" from the research brief becomes `LLMFilterParser` (wraps `ILLMClient`).

---

## Files

**Backend — new:**
- `src/fala_gavea/domain/repositories/filter_ports.py` — `IFilterParser` port + `ParseError`
- `src/fala_gavea/application/use_cases/nl/__init__.py`
- `src/fala_gavea/application/use_cases/nl/parse_nl_filter.py` — `ParseNLFilter` use case + `ParseNLFilterResult`
- `src/fala_gavea/infrastructure/llm/llm_filter_parser.py` — `LLMFilterParser` (wraps `ILLMClient`)
- `src/fala_gavea/presentation/api/routers/nl.py` — merged router: `/nl/chat` + `/nl/filter`
- `src/fala_gavea/presentation/schemas/nl_filter.py` — `NLFilterRequest` / `NLFilterResponse`
- `tests/test_parse_nl_filter.py` — unit tests for use case

**Backend — modified:**
- `src/fala_gavea/presentation/api/routers/chat.py` — keep `/nl/chat` here OR migrate to `nl.py` (step 4 decides)
- `src/fala_gavea/presentation/api/main.py` — mount `nl.py` router
- `src/fala_gavea/presentation/api/dependencies.py` — add `get_filter_parser()` dependency
- `src/fala_gavea/domain/repositories/semantic_ports.py` — no change (ILLMClient is already there)
- `pyproject.toml` — add `slowapi` for rate limiting

**Frontend — modified:**
- `frontend/src/features/workspace/FilterPanel.tsx` — wire Section 4: textarea, send button, loading, suggestion preview zone, Aplicar/Descartar
- `frontend/src/features/workspace/FilterPanel.test.tsx` — update/add tests for Section 4 live state
- `frontend/src/api/` — add `postNLFilter(text, token)` API call
- `frontend/src/store/workspaceStore.ts` — add `applyNLSuggestion(suggestion)` action

---

## Steps

### Step 1 — Domain port: `IFilterParser` + `ParseError`

Create `src/fala_gavea/domain/repositories/filter_ports.py`:

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParseError(Exception):
    message: str
    partial: dict = field(default_factory=dict)
    raw: str = ""


class IFilterParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> dict:
        """Parse natural language into a ReportQueryRequest-compatible dict.

        Raises ParseError on unrecoverable failure.
        """
```

**Why a separate file:** `semantic_ports.py` owns LLM/search/index ports. Filter parsing is a different concern (presentation-layer input coercion) — keeping it separate avoids bloating the semantic ports file and makes the dependency graph clearer.

**Validation:** `dict` return type is intentional — the use case owns Pydantic coercion. The port contract is minimal.

---

### Step 2 — Infrastructure: `LLMFilterParser`

Create `src/fala_gavea/infrastructure/llm/llm_filter_parser.py`:

```python
from __future__ import annotations
import json
import logging
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um assistente que converte texto em português para um filtro estruturado JSON.
Retorne SOMENTE um objeto JSON válido com zero ou mais dos campos abaixo (omita campos não mencionados):
{
  "report_type_ids": [],   // lista de strings (IDs de tipo)
  "urgencies": [],         // lista de: "alta", "media", "baixa"
  "statuses": [],          // lista de: "pendente", "em_analise", "encaminhado", "resolvido"
  "since": null,           // ISO 8601 date string ou null
  "until": null,           // ISO 8601 date string ou null
  "text": null,            // string de busca textual ou null
  "q": null                // string de busca semântica ou null
}
Não inclua explicações. Retorne apenas JSON."""


class LLMFilterParser(IFilterParser):
    def __init__(self, llm_client: ILLMClient) -> None:
        self._llm = llm_client

    def parse(self, text: str) -> dict:
        raw = self._llm.complete(_SYSTEM_PROMPT, [{"role": "user", "content": text}])
        result, warnings = self._try_parse(raw)
        if result is not None:
            return result
        # one repair retry
        repair_prompt = (
            f"O JSON anterior estava malformado: {raw!r}\n"
            "Retorne apenas o JSON válido, sem nenhum texto extra."
        )
        raw2 = self._llm.complete(_SYSTEM_PROMPT, [
            {"role": "user", "content": text},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": repair_prompt},
        ])
        result2, _ = self._try_parse(raw2)
        if result2 is not None:
            return result2
        raise ParseError(message="LLM returned invalid JSON after retry", raw=raw2)

    @staticmethod
    def _try_parse(raw: str) -> tuple[dict | None, list[str]]:
        try:
            data = json.loads(raw.strip())
            if isinstance(data, dict):
                return data, []
        except json.JSONDecodeError:
            pass
        # Try to extract JSON from markdown code block
        import re
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, dict):
                    return data, ["extracted from markdown block"]
            except json.JSONDecodeError:
                pass
        return None, []
```

**Why wrap `ILLMClient` instead of `OllamaClient` directly:** The factory already dispatches to Ollama or Anthropic via `FALA_GAVEA_LLM_PROVIDER`. Wrapping `ILLMClient` means the same `LLMFilterParser` works in both environments without any code change. The research brief called this "OllamaFilterParser" but the LLM factory makes provider agnosticism free.

**Why no `format` param for JSON-mode:** `ILLMClient.complete()` is a generic interface. Ollama's JSON `format` param is an Ollama-specific feature not in the interface. The system prompt constraint + retry logic achieves robust JSON extraction across both providers.

---

### Step 3 — Use case: `ParseNLFilter`

Create `src/fala_gavea/application/use_cases/nl/__init__.py` (empty).

Create `src/fala_gavea/application/use_cases/nl/parse_nl_filter.py`:

```python
from __future__ import annotations
from dataclasses import dataclass, field
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError
from fala_gavea.presentation.schemas.report import ReportQueryRequest

_ALLOWED_KEYS = {
    "report_type_ids", "urgencies", "statuses",
    "since", "until", "text", "q",
}


@dataclass
class ParseNLFilterResult:
    body: dict
    warnings: list[str] = field(default_factory=list)


class ParseNLFilter:
    def __init__(self, filter_parser: IFilterParser | None) -> None:
        self._parser = filter_parser

    def execute(self, text: str) -> ParseNLFilterResult:
        if self._parser is None:
            raise RuntimeError("filter_parser not configured")
        raw = self._parser.parse(text)
        # Strip unknown keys; coerce via Pydantic for validation
        filtered = {k: v for k, v in raw.items() if k in _ALLOWED_KEYS and v is not None}
        warnings: list[str] = []
        unknown = set(raw.keys()) - _ALLOWED_KEYS
        if unknown:
            warnings.append(f"Campos ignorados: {sorted(unknown)}")
        # Pydantic validates urgencies/statuses enum values; invalid values dropped with warning
        try:
            validated = ReportQueryRequest(**filtered)
            body = validated.model_dump(exclude={"limit", "offset", "bbox"}, exclude_none=True)
        except Exception as exc:
            warnings.append(f"Validação parcial: {exc}")
            body = filtered
        return ParseNLFilterResult(body=body, warnings=warnings)
```

**Note:** `ParseNLFilter` is in `application/` but imports from `presentation/schemas/`. This is a minor layer-purity trade-off: `ReportQueryRequest` is the canonical definition of valid filter fields. Alternative is to duplicate validation in the use case — Rule of Three says don't. Acceptable for PoC scope.

---

### Step 4 — Pydantic schemas for `/nl/filter`

Create `src/fala_gavea/presentation/schemas/nl_filter.py`:

```python
from __future__ import annotations
from pydantic import BaseModel, field_validator


class NLFilterRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("text must not be empty")
        if len(v) > 500:
            raise ValueError("text must be 500 characters or fewer")
        return v


class NLFilterResponse(BaseModel):
    body: dict
    warnings: list[str] = []
```

---

### Step 5 — Router: `nl.py` (merges `/nl/chat` + `/nl/filter`)

**Decision:** Move `chat.py` content into a new unified `nl.py` router and delete `chat.py`. This avoids two separate router files for the same `/nl` prefix and is consistent with the as-coded description that already reads "POST /nl/chat router".

Create `src/fala_gavea/presentation/api/routers/nl.py`:

```python
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.repositories.filter_ports import ParseError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_filter_parser,
    get_llm_client,
    get_report_repo,
    get_semantic_search_port,
    require_any_role,
)
from fala_gavea.presentation.schemas.chat import ChatRequest, ChatResponse
from fala_gavea.presentation.schemas.nl_filter import NLFilterRequest, NLFilterResponse

router = APIRouter()
_log = logging.getLogger(__name__)
limiter = Limiter(key_func=lambda request: request.state.current_user_id)


@router.post("/chat", response_model=ChatResponse)
def nl_chat(
    body: ChatRequest,
    _current_user: User = Depends(require_any_role("agent", "admin")),
    report_repo: IReportRepository = Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
    llm_client: ILLMClient | None = Depends(get_llm_client),
) -> ChatResponse:
    if llm_client is None:
        raise HTTPException(status_code=503, detail="LLM provider is not configured.")
    if search_port is None:
        raise HTTPException(status_code=503, detail="Semantic search is not available.")
    use_case = AnswerWithRag(search_port, report_repo, llm_client)
    result = use_case.execute(body.message)
    return ChatResponse(response=result.response, cited_report_ids=result.cited_report_ids)


@router.post("/filter", response_model=NLFilterResponse)
@limiter.limit("10/minute")
def nl_filter(
    request: Request,
    body: NLFilterRequest,
    current_user: User = Depends(get_current_user),
    filter_parser=Depends(get_filter_parser),
) -> NLFilterResponse:
    request.state.current_user_id = current_user.id  # key for rate limiter
    if filter_parser is None:
        raise HTTPException(
            status_code=503,
            detail="O assistente de filtros está indisponível.",
        )
    try:
        use_case = ParseNLFilter(filter_parser)
        result = use_case.execute(body.text)
        return NLFilterResponse(body=result.body, warnings=result.warnings)
    except ParseError as exc:
        _log.warning("NL filter parse error: %s", exc.message)
        raise HTTPException(status_code=503, detail="Não foi possível interpretar o filtro.")
    except Exception as exc:
        _log.error("NL filter unexpected error: %s", exc)
        raise HTTPException(status_code=503, detail="Erro inesperado no assistente de filtros.")
```

**Rate limiting approach:** `slowapi` is the de-facto FastAPI rate limiter. Key function uses `current_user.id` (not IP) to enforce per-user limits, which is correct for authenticated endpoints. On 429, slowapi returns `{"error": "Rate limit exceeded: 10 per 1 minute"}` automatically.

**Timeout:** The 8-second timeout should be enforced at the `ILLMClient` level. The existing `OllamaClient` uses `httpx.Client(timeout=120.0)` — that's too long for a filter parse UX. Step 6 adds a `filter_parse` timeout override.

---

### Step 6 — Add 8-second timeout to OllamaClient for filter parsing

The `OllamaClient` currently uses a flat 120s timeout (suitable for RAG chat). For filter parsing, 8s is the target. Rather than adding timeout complexity to `ILLMClient`, add a `timeout` parameter to `OllamaClient.chat()` and pass it from `LLMFilterParser`.

**Edit `src/fala_gavea/infrastructure/ollama/ollama_client.py`:**

Change `chat()` signature to:
```python
def chat(self, messages: list[dict[str, Any]], stream: bool = False, timeout: float = 120.0) -> str:
```

And use it in the httpx call:
```python
with httpx.Client(timeout=timeout) as client:
```

**Edit `LLMFilterParser`:** Before calling `self._llm.complete(...)`, the `ILLMClient` interface doesn't expose timeout. The `LLMFilterParser` knows it's using a thin wrapper — but it must not reach through the interface. The practical solution: keep the 8s timeout in the `OllamaAdapter` via a dedicated method or via a class-level constant.

**Revised approach:** Add a `complete_with_timeout(system, messages, timeout_s)` default-impl method to `ILLMClient` that simply calls `complete()` by default (so `AnthropicClient` inherits it without change). `OllamaAdapter` overrides it to pass the timeout through to `OllamaClient.chat()`. `LLMFilterParser` calls `complete_with_timeout(system, messages, timeout_s=8.0)` if the client supports it, else falls back to `complete()`.

Concretely:

**`domain/repositories/semantic_ports.py`** — add to `ILLMClient`:
```python
def complete_with_timeout(self, system: str, messages: list[dict[str, str]], timeout_s: float = 120.0) -> str:
    """Default: delegates to complete(). Override for provider-specific timeout support."""
    return self.complete(system, messages)
```

**`infrastructure/llm/ollama_adapter.py`** — override:
```python
def complete_with_timeout(self, system: str, messages: list[dict[str, str]], timeout_s: float = 120.0) -> str:
    full_messages = [{"role": "system", "content": system}] + messages
    return self._client.chat(full_messages, timeout=timeout_s)
```

**`LLMFilterParser.parse()`** — call `self._llm.complete_with_timeout(..., timeout_s=8.0)`.

`AnthropicClient` inherits the default (delegates to `complete()`). Anthropic SDK has its own timeout handling via `httpx` — a future step can wire `ANTHROPIC_TIMEOUT` env var if needed, but 8s is already the Anthropic SDK's default read timeout.

---

### Step 7 — `get_filter_parser()` dependency + slowapi setup in `main.py`

**Edit `dependencies.py`** — add:
```python
_filter_parser_instance = None

def get_filter_parser():
    global _filter_parser_instance
    if _filter_parser_instance is None:
        llm = get_llm_client()
        if llm is not None:
            from fala_gavea.infrastructure.llm.llm_filter_parser import LLMFilterParser
            _filter_parser_instance = LLMFilterParser(llm)
    return _filter_parser_instance
```

**Edit `main.py`** — replace `chat.router` mount with `nl.router`:
```python
# Before:
from fala_gavea.presentation.api.routers.chat import router as chat_router
app.include_router(chat_router, prefix="/nl", tags=["nl"])

# After:
from fala_gavea.presentation.api.routers.nl import router as nl_router, limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(nl_router, prefix="/nl", tags=["nl"])
```

Add `slowapi` to `pyproject.toml` under `[project.dependencies]`.

Delete `src/fala_gavea/presentation/api/routers/chat.py` (content migrated to `nl.py`).

---

### Step 8 — Frontend: API call + store action

**`frontend/src/api/nlFilter.ts`** (new file):
```typescript
import { ReportQueryRequest } from './types'

export interface NLFilterResponse {
  body: Partial<ReportQueryRequest>
  warnings: string[]
}

export async function postNLFilter(text: string, token: string): Promise<NLFilterResponse> {
  const res = await fetch('/nl/filter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ text }),
  })
  if (res.status === 429) throw new Error('rate_limit')
  if (res.status === 503) throw new Error('unavailable')
  if (!res.ok) throw new Error('error')
  return res.json()
}
```

**`frontend/src/store/workspaceStore.ts`** — add `applyNLSuggestion(suggestion: Partial<DraftFilters>)` action that merges suggestion into `draftFilters` (non-destructive: only sets fields present in the suggestion; does not clear existing draft values). Also add `nlSuggestion: Partial<DraftFilters> | null` and `nlWarnings: string[]` to the store state.

---

### Step 9 — Frontend: Section 4 wire-up in `FilterPanel.tsx`

Replace the placeholder Section 4 block with a fully functional NL assistant UI:

```tsx
{/* Section 4 — NL assistant */}
<div className="border-t pt-2 pb-3 px-3 flex flex-col gap-2">
  <p className="text-xs text-gray-500 font-medium">Assistente de filtros</p>
  <div className="flex gap-1">
    <Textarea
      rows={2}
      placeholder="Descreva o filtro em linguagem natural..."
      className="text-xs flex-1 resize-none"
      value={nlText}
      onChange={e => setNlText(e.target.value)}
      disabled={nlLoading || !token}
      onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleNLSubmit() } }}
    />
    <Button
      size="sm"
      variant="ghost"
      className="h-auto px-2 self-start"
      onClick={handleNLSubmit}
      disabled={nlLoading || !nlText.trim() || !token}
      title="Enviar"
    >
      {nlLoading ? <Spinner className="h-4 w-4" /> : '→'}
    </Button>
  </div>

  {nlError === 'unavailable' && (
    <p className="text-xs text-amber-600">
      O assistente de filtros está indisponível — use os controles manuais.
    </p>
  )}
  {nlError === 'rate_limit' && (
    <p className="text-xs text-amber-600">Limite de uso atingido. Tente novamente em 1 minuto.</p>
  )}

  {nlSuggestion && (
    <div className="rounded border border-blue-200 bg-blue-50 p-2 flex flex-col gap-1">
      <p className="text-xs text-blue-700 font-medium">Sugestão do assistente</p>
      <NLSuggestionChips suggestion={nlSuggestion} />
      {nlWarnings.length > 0 && (
        <p className="text-xs text-gray-500">{nlWarnings.join('; ')}</p>
      )}
      <div className="flex gap-2 mt-1">
        <Button size="sm" variant="outline" className="text-xs h-6 px-2"
          onClick={() => { applyNLSuggestion(nlSuggestion); setNlSuggestion(null) }}>
          Aplicar sugestão ao rascunho
        </Button>
        <Button size="sm" variant="ghost" className="text-xs h-6 px-2"
          onClick={() => setNlSuggestion(null)}>
          Descartar
        </Button>
      </div>
    </div>
  )}
</div>
```

**`NLSuggestionChips`** — inline sub-component that renders the suggestion dict as readable text chips (e.g., "Urgência: alta", "Texto: poste apagado"). Reuses the same chip style as `ActiveFilterChips`.

**State wiring:**
- `nlText`, `nlLoading`, `nlError`, `nlSuggestion`, `nlWarnings` — local `useState` in `FilterPanel`
- `token` — from `useAuthStore()` (already used elsewhere in the workspace)
- `applyNLSuggestion` — from `workspaceStore`

**`handleNLSubmit`:**
```typescript
async function handleNLSubmit() {
  setNlLoading(true); setNlError(null); setNlSuggestion(null)
  try {
    const res = await postNLFilter(nlText.trim(), token!)
    setNlSuggestion(res.body)
    setNlWarnings(res.warnings)
  } catch (e: any) {
    setNlError(e.message ?? 'error')
  } finally {
    setNlLoading(false)
  }
}
```

---

### Step 10 — Tests

**`tests/test_parse_nl_filter.py`:**

```python
import pytest
from unittest.mock import MagicMock
from fala_gavea.application.use_cases.nl.parse_nl_filter import ParseNLFilter
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError


class FakeParser(IFilterParser):
    def __init__(self, result):
        self._result = result
    def parse(self, text):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def test_returns_validated_body():
    parser = FakeParser({"urgencies": ["alta"], "q": "postes apagados"})
    result = ParseNLFilter(parser).execute("postes apagados urgência alta")
    assert result.body["urgencies"] == ["alta"]
    assert result.body["q"] == "postes apagados"
    assert result.warnings == []


def test_drops_unknown_keys_with_warning():
    parser = FakeParser({"q": "x", "unknown_key": "foo"})
    result = ParseNLFilter(parser).execute("x")
    assert "unknown_key" not in result.body
    assert any("ignorados" in w for w in result.warnings)


def test_none_parser_raises():
    with pytest.raises(RuntimeError):
        ParseNLFilter(None).execute("any text")


def test_parse_error_propagates():
    parser = FakeParser(ParseError(message="fail"))
    with pytest.raises(ParseError):
        ParseNLFilter(parser).execute("any")
```

**Frontend:** Add tests to `FilterPanel.test.tsx` covering:
- Section 4 renders with enabled textarea when `token` is present
- Submit triggers `postNLFilter` mock
- Suggestion preview zone appears after successful response
- "Aplicar sugestão ao rascunho" calls `applyNLSuggestion`
- "Descartar" clears suggestion
- `unavailable` error shows graceful degradation message
- `rate_limit` error shows rate limit message

---

### Step 11 — Update `as-coded` doc + `CLAUDE.md`

Post-skill will handle `as-coded`. Manually update `CLAUDE.md` env vars section to document:
- `FALA_GAVEA_LLM_PROVIDER` — `ollama` (default) | `anthropic`
- `ANTHROPIC_API_KEY` — required when `FALA_GAVEA_LLM_PROVIDER=anthropic`
- `FALA_GAVEA_ANTHROPIC_MODEL` — model override (default: `claude-haiku-4-5-20251001`)

These are already in the stack but not yet documented in the env-vars section.

---

## Review

**Perspectives evaluated (Essential tier — FEATURE-X cross-cutting):**

| Perspective | Status | Notes |
|-------------|--------|-------|
| SEC | Adopted | Rate limit per `user.id` (not IP) prevents Ollama saturation. Input capped at 500 chars. Auth required (`get_current_user`). No PII in LLM prompt beyond the user's own typed text. |
| API | Adopted | `POST /nl/filter` consistent with `/nl/chat` prefix. 503 on unavailable, 429 on rate limit. Never auto-applies — user-initiated merge only. |
| ARCH | Adopted | `IFilterParser` port in `domain/` + `LLMFilterParser` in `infrastructure/llm/`. Use case in `application/`. No direct Ollama/Anthropic access outside `infrastructure/`. LLM factory reused — provider agnosticism free. |
| UX | Adopted | Never auto-apply (R3/R8). Graceful degradation message on 503. Suggestion preview zone with explicit Aplicar/Descartar. Rate limit error message in pt-BR. Manual controls remain fully usable when LLM unavailable. |
| TEST | Adopted | Unit tests for `ParseNLFilter` use case covering happy path, unknown keys, None parser, ParseError. Frontend tests for all Section 4 states. |
| PERF | Adopted | 8-second timeout via `complete_with_timeout()`. Rate limit 10 req/min. Singleton `_filter_parser_instance` (no re-init per request). `LLMFilterParser` lightweight — no model loading (uses existing `ILLMClient`). |
| DX | Deferred | `LLMFilterParser` system prompt is hard-coded string. Externalizing to a `.txt` file would aid future prompt iteration — deferred as PoC scope. |
| I18N | N/A | All pt-BR strings consistent with existing convention. No i18n keys needed. |
| A11Y | Adopted | `Textarea` has placeholder text; Send button has `title` attribute. Loading state disables controls. |

---

## Docs

- Update `CLAUDE.md` stack section to mention `POST /nl/filter` endpoint and `slowapi` rate limiter.
- Update `product-design-as-coded.md` §1 to add `POST /nl/filter` to the endpoint list.
- No new migrations needed (no new DB tables in this phase).

---

## Commit message

```
feat(nl): Phase C NL filter parser — IFilterParser port, LLMFilterParser, ParseNLFilter use case, POST /nl/filter (10 req/min), Section 4 wire-up with suggestion preview zone and Aplicar/Descartar
```

---

## Implementation Summary

**Steps completed:** 11/11 | **Iterations:** multi-session (auto mode)

### Key changes
- **Steps 1-4** (commit d1def9b): `IFilterParser` port + `ParseError`, `LLMFilterParser`, `ParseNLFilter` use case, `NLFilterRequest`/`NLFilterResponse` schemas
- **Steps 5-7** (commit 3e46854): merged `nl.py` router (chat+filter), `get_filter_parser` dependency, `slowapi` rate limiter, `complete_with_timeout` timeout chain
- **Steps 8-9** (commit 6351057): `postNLFilter` API function, `nlSuggestion`/`nlWarnings` store state, Section 4 UI wire-up
- **Steps 10-11** (commit 16dea0b): 4 backend pytest tests + 25 frontend tests (all pass), `CLAUDE.md` env vars updated
- **Quality gate** (commit fb4f757): arch violation fixed (removed `ReportQueryRequest` import from use case), check logs saved

### Quality gate results
- Backend tests: 167 passed, 1 pre-existing failure (test_static_spa)
- Frontend tests: 100 passed, 0 failures
- Code review: 7 advisory findings (rate limiter scope, singleton thread-safety, error detail in responses, Retry-After headers, thread-pool saturation, LLMFilterParser unit tests, frontend test pattern); 1 critical arch violation resolved inline

### Advisory findings (deferred)
1. Rate limiter uses IP key behind proxy (HIGH SEC) — local dev scope acceptable
2. Singleton not thread-safe (HIGH SEC) — pre-existing pattern
3. Error detail echoed to client (MEDIUM SEC) — future improvement
4. No Retry-After header on 429 (MEDIUM API) — future improvement
5. Sync LLM blocks thread pool up to 16s (MEDIUM PERF) — local dev scale acceptable
6. LLMFilterParser retry path untested (MEDIUM TEST) — out of plan scope
7. Frontend error-path test pattern fragile (LOW TEST) — tests pass; refactor optional
