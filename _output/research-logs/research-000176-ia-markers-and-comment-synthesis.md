# Research 000176 | TB | 2026-06-26 11:40 UTC | IA markers on AI features + forwarding comment synthesis
tags: metacommunication, ux, accessibility, security-privacy, llm, frontend
spawned: plan-000178, plan-000179

## User brief

> ADD IA marker on all features on site that use IA para sugerir algo (ReportTypes), síntese de comentarios de encaminhamentos (Este aqui não temos. podemos fazer um plano para isso)

## Agent interpretation

Two distinct deliverables:

- **A — IA markers (signposts):** add a consistent visual marker on every UI feature that uses AI to suggest/generate content, replacing today's ad-hoc `(IA)` text labels with one reusable component.
- **B — Forwarding comment synthesis (NEW):** an AI feature that summarizes the comment thread of an *encaminhamento* (forwarding). It does not exist yet; this research maps its design space and feeds a `/plan`.

## Files examined

- `frontend/src/features/workspace/ViewToggleBar.tsx` — ad-hoc `(IA)` label (chat tab) at line 18
- `frontend/src/features/workspace/FilterPanel.tsx` — "Assistente de filtros" / "Assistente de IA" labels (468, error copy 174, `aria-live` precedent 442)
- `frontend/src/features/workspace/views/ChatView.tsx` — RAG chat surface
- `frontend/src/hooks/useChat.ts`, `useKeywords.ts` — AI hooks
- `frontend/src/components/CommentSection.tsx` — where the summary button/output belongs
- `frontend/src/features/forwardings/ForwardingRow.tsx` (CommentSection at 63), `PublicForwardingRow.tsx` (CommentSection at 117)
- `src/fala_gavea/presentation/api/routers/nl.py` — POST + role-guard + 503 patterns to mirror
- `src/fala_gavea/presentation/api/routers/comments.py` — **`list_comments` (22) has NO auth dependency**
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` — use-case template
- `src/fala_gavea/domain/entities/comment.py` — `Comment{id, forwarding_id, author_id, text, created_at}`
- `src/fala_gavea/domain/repositories/semantic_ports.py` — `ILLMClient`, `ISemanticSearchPort`
- `_output/plans/plan-000174-pluggable-report-type-suggestion.md` — report-type suggestion (planned, not built)

---

## AI feature inventory (current state)

| # | Feature | Where | Roles | AI marker today |
|---|---------|-------|-------|-----------------|
| 1 | NL Chat / RAG assistant | `ChatView` tab in workspace | agent/admin | `(IA)` in `ViewToggleBar` tooltip only |
| 2 | NL filter assistant | `FilterPanel` "Assistente de filtros" | all | "Assistente de filtros" / error says "Assistente de IA" |
| 3 | Semantic search | `semanticQuery` filter (FilterPanel) | all | none |
| 4 | Auto keyword suggestions | `useKeywords` | workspace | none — **user excluded from scope** |
| 5 | Report-type suggestion | plan-000174 (not built) | agent/admin | n/a — mark when built |
| 6 | **Forwarding comment synthesis** | *to build* (Deliverable B) | agent/admin | n/a |

User confirmed marker scope = **#1, #2 (+ its semantic search), #5**. #4 excluded.

---

## Decisions captured this session (from AskUserQuestion)

- **Marker visual:** icon-only ✨ (sparkles) + tooltip.
- **Marker scope:** Chat NL (RAG), Filtro NL + busca semântica, Sugestão de tipo de relato.
- **Synthesis trigger/audience:** on-demand button ("Resumir comentários (IA)"), agents/admin only.
- **Synthesis LLM:** follow the configured `ILLMClient` provider (Ollama or Anthropic per `FALA_GAVEA_LLM_PROVIDER`).

---

## Deliverable A — IA marker component

**Recommendation:** build one reusable `frontend/src/components/AiBadge.tsx` and apply it at the three confirmed sites, retiring the ad-hoc `(IA)` literals.

- **Visual:** the user chose icon-only ✨ + tooltip. The expert review flags this as an accessibility/metacommunication risk (a bare sparkle does not say "AI-generated, may be wrong"; tooltips are unreliable on touch/keyboard, and an icon-only element lacks an accessible name). **Minimum floor if kept icon-only:** `aria-label="Gerado por IA"` + a keyboard/focus-reachable tooltip. **Recommended:** icon + short visible "IA" text + tooltip — still compact, satisfies the intent, and gives the accessible name for free. Decide this explicitly at `/plan`.
- **Tooltip copy (pt-BR):** e.g. "Conteúdo gerado por IA — pode conter erros. Revise antes de agir."
- **Consistency:** replace the literal at `ViewToggleBar.tsx:18` and the "Assistente de filtros" label at `FilterPanel.tsx:468`; reserve a slot for report-type suggestion when plan-000174 lands.
- **No backend / no i18n framework:** the project hardcodes pt-BR strings; match that convention, don't introduce keys.

This is low-risk frontend-only work — a small `/plan` (or even `/plan --light`) suffices.

---

## Deliverable B — Forwarding comment synthesis (design space → plan)

Comments already exist (`Comment{id, forwarding_id, author_id, text}`), attached to forwardings, authored by **citizens and agents**, shown in `CommentSection`. The feature adds an agent-triggered AI summary of that thread.

### Architecture (fits existing clean-arch patterns)
- New use case `SummarizeForwardingComments` in `application/use_cases/comments/`, depending on `ICommentRepository` + `ILLMClient` (no new port). Mirror `AnswerWithRag`.
- New endpoint **`POST /forwardings/{id}/comments/summary`** (POST, not GET: generation is non-idempotent/non-cacheable; matches `/chat`, `/filter`). Construct the use case in the router like `nl.py:55`. Return `{ summary, comment_count, generated_at }`.
- **Guard with `require_any_role("agent", "admin")`** (CONVENTION_2 / `dependencies.py`).
- **Ephemeral:** do NOT persist or cache the summary server-side, do NOT index in ChromaDB. This eliminates retention / right-to-deletion / staleness obligations and matches the local Ollama deployment. Optional short-lived *client*-side cache keyed on comment count if latency bites.

### Security / privacy (HIGH)
- **Prompt injection:** comment text is fully citizen-controlled and flows into the prompt. Mitigate: wrap comment text in explicit delimiters, place it in a **`user` message (not `system`)** — deliberately deviating from `AnswerWithRag`'s system-prompt concatenation — instruct the model to treat it as data, cap total input length, and render output as **plain text** (never HTML/markdown).
- **PII:** citizen comments may carry names/addresses/plates/phones. Ephemeral summary (above) minimizes the derived-data footprint. Keep summaries off the public view (agents-only, per user).
- **Pre-existing exposure to flag (out of scope to fix here):** `list_comments` (`comments.py:22`) has **no auth dependency** and returns `author_id`, and `CommentSection` is rendered on `PublicForwardingRow.tsx:117` — so comments + `author_id` are already publicly readable. The summary feature makes this more consequential. Confirm intended or fix separately; do NOT wire the summary into the public row.

### UX (MEDIUM)
- Button "Resumir comentários (IA)" at the top of the comment list in `CommentSection`, gated on `user.role ∈ {agent, admin}`, carrying the `AiBadge`.
- States: loading ("Resumindo…"), error, and **503 unavailable** with copy matching `nl.py:74` ("O assistente … está indisponível no momento.").
- **Staleness:** stamp "Resumo de N comentários · <hora>"; when the comments query count changes after generation, show "Comentários novos desde este resumo — gerar novamente." (`CommentSection` already invalidates the comments query on add, so this is cheap client-side).
- **A11Y:** render the summary in an `aria-live="polite"` container (precedent `FilterPanel.tsx:442`); keyboard-operable trigger with visible focus ring.

### Suggested plan shape
Backend: use case + router endpoint + Pydantic schema + tests (success, empty thread, 503 unconfigured LLM, role guard). Frontend: summary button + output block + states in `CommentSection` + the shared `AiBadge`. One standard `/plan` covers B; A can ride along or be a separate `--light` plan.

---

## Q&A log

**Q1 (initial brief):** ADD IA marker on all features on site that use IA para sugerir algo (ReportTypes), síntese de comentarios de encaminhamentos (Este aqui não temos. podemos fazer um plano para isso)

**A1:** The app has 5 AI touchpoints (chat/RAG, NL filter, semantic search, auto-keywords, planned report-type suggestion); markers today are inconsistent ad-hoc `(IA)` text. Recommend one reusable `AiBadge` applied at the confirmed sites. "Síntese de comentários de encaminhamentos" maps to summarizing a forwarding's existing comment thread — comments already exist (`Comment.forwarding_id`); the feature is an agent-triggered, ephemeral AI summary behind `ILLMClient`, exposed via `POST /forwardings/{id}/comments/summary` guarded to agents/admin, with prompt-injection and PII mitigations and staleness handling. A pre-existing issue surfaced: `list_comments` is unauthenticated and rendered on the public forwarding view.

**Clarifications (AskUserQuestion):** marker = icon-only ✨ + tooltip; scope = chat / NL filter+semantic / report-type suggestion; synthesis = on-demand button, agents-only; synthesis LLM = configured provider.

---

## Recommendations summary

1. **[HIGH]** Synthesis endpoint `POST /forwardings/{id}/comments/summary` guarded `require_any_role("agent","admin")`; never render in `PublicForwardingRow`.
2. **[HIGH]** Prompt-injection hardening: delimit comment text, put it in a `user` message (not `system`), cap length, render output as plain text.
3. **[HIGH]** Keep the summary ephemeral — no server persistence/caching, no ChromaDB indexing.
4. **[HIGH]** Accessibility floor for both: `AiBadge` needs an accessible name; summary in an `aria-live="polite"` region; keyboard-operable controls.
5. **[MEDIUM]** Build `AiBadge` as icon + short "IA" text + tooltip (recommended over icon-only); apply at ChatView/ViewToggleBar, FilterPanel assistant, and report-type suggestion (when plan-000174 lands).
6. **[MEDIUM]** Summary UX: button atop `CommentSection` (agent/admin), loading/error/503 states mirroring `nl.py`, staleness hint on comment-count change, output block carrying `AiBadge`.
7. **[MEDIUM]** Use case `SummarizeForwardingComments` (application/use_cases/comments) via `ILLMClient`; return `{summary, comment_count, generated_at}`.
8. **[LOW]** Flag pre-existing exposure: `list_comments` is unauthenticated and shown on the public view — confirm intended or fix separately (out of scope here).
9. **[LOW]** Hardcode pt-BR copy (no i18n framework); dates via `toLocaleDateString("pt-BR")`.
