# QA Log — plan-000140 | 2026-06-21 22:49 UTC | Phase C NL filter parser backend and NL assistant UX

## Brief

Phase C (new plan): NL filter parser backend (`IFilterParser` port + `OllamaFilterParser` + `ParseNLFilter` use case + `POST /nl/filter` endpoint) + NL assistant UX (Section 4 input, suggestion preview zone, "Aplicar sugestão" button). From research 136.

## Q&A Log

**Q: Can we use the Anthropic API in production for the NL filter parser instead of Ollama?**

A: Yes. The `anthropic` SDK is already in the project dependencies. An `AnthropicClient` wrapping `ILLMClient` already exists in `infrastructure/llm/anthropic_client.py`, and the `factory.py` dispatches to it via `FALA_GAVEA_LLM_PROVIDER=anthropic`. The `LLMFilterParser` in this plan wraps `ILLMClient` (not `OllamaClient` directly), so it works with both providers transparently. Set `ANTHROPIC_API_KEY` + `FALA_GAVEA_LLM_PROVIDER=anthropic` in production env vars — no code change needed.

**Key design decisions documented in plan-000140:**

1. `LLMFilterParser` wraps `ILLMClient` (not `OllamaClient`) for provider agnosticism — same implementation works with Ollama locally and Anthropic in production.
2. `complete_with_timeout()` default-impl added to `ILLMClient`; `OllamaAdapter` overrides it for 8s timeout; `AnthropicClient` inherits the default.
3. `/nl/chat` and `/nl/filter` merged into a single `nl.py` router for consistent prefix management.
4. Rate limit 10 req/min per `user.id` via `slowapi`; returns 429 with retry-after.
5. Never auto-apply — suggestion preview zone with explicit "Aplicar sugestão" / "Descartar" buttons.
6. Graceful 503 degradation: Section 4 shows inline error; manual controls remain fully usable.
