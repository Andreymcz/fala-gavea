# Research 000180 | fala-gavea | 2026-06-26 13:10 UTC | SEJA methodology in the platform-helper system prompt (dogfooding)

source: follows plan-000177 (chat-helper RAG sobre self-docs, D-014)
tags: rag, system-prompt, metacommunication, security, architecture, dogfooding

## User brief

> following chat helper from plan 177, can we add SEJA skill into chat context to harness the chat itself?

Clarified via AskUserQuestion:
- **"SEJA skill" = methodology in the system prompt** — bake SEJA's concepts/taxonomy (doc_type, plan/research/decision structure) into the helper's system prompt so it interprets the indexed self-docs more intelligently. *Not* indexing `.claude/skills` into the RAG corpus, and *not* runtime skill invocation.
- **Goal = self-aware / dogfooding demo** — showcase that the app is built with SEJA and the chat is aware of its own development process; a meta angle for the course.

## Agent interpretation

The platform-helper chat from plan-000177 (`AnswerHelpWithRag` → `POST /nl/help`, Step 5 not yet implemented) already does RAG over the project's own SEJA-generated docs with a role_visibility filter (citizen/agent → `public`; admin → `public`+`internal`). The user wants to enrich its **system prompt** (`_SYSTEM_PT_BR`) with SEJA methodology/taxonomy knowledge so the deputy reads the indexed self-docs more intelligently and presents itself as built-with-SEJA — a metacommunication/dogfooding artifact for an AI Systems Design (Semiotic Engineering) course at PUC-Rio. The change is static prompt text only — no new corpus, no agentic tool-use.

**Answer: Yes — this is a cheap, on-theme change that folds into plan-000177 Step 5 (+ a small Step 6 touch), with three guardrails.** It is genuinely a strong SemEng demo *if* the "self-aware" framing is narrowed to **honest provenance disclosure** rather than anthropomorphic identity claims.

> **[REFINED 2026-06-26 — plan-000177 now IMPLEMENTED]** The recommendations below are unchanged in substance, but they are no longer plan amendments — they are concrete edits to shipped code. See the **Follow-up Q&A (2026-06-26)** section at the end for the file/line-level mapping against the real `answer_help_with_rag.py`, `nl.py`, and `chat.py`.

## Files

Read / relevant:
- `_output/plans/plan-000177-chat-helper-plataforma-rag-self-docs.md` — Step 5 (`_SYSTEM_PT_BR`, not-found path) and Step 6 (schema + router `_ROLE_VISIBILITY`, `meta_mode`) are where this lands.
- `_output/research-logs/research-000175-chat-helper-rag-documentacao.md` — origin of the role_visibility / default-deny security model.
- `product-design/project/product-design-as-coded.md` §4 (line 195) — the **committed metamessage**: "The AI appears as just another lens of exploration, always citing where it drew its answers from — assistance, not decision."
- `product-design/project/constitution.md` — T1 (LLM/semantic access only via `infrastructure/`), T2 (auth decisions only in `dependencies.py`/router), C1 (citizen data stays local).

---

## Perspective synthesis

| Perspective | Verdict | Essence |
|---|---|---|
| **SemEng / Metacommunication** (primary) | ✅ Adopt, reframed | The deputy disclosing its own provenance ("my knowledge base is the platform's design docs, and I always cite") is on-message with the established metamessage and is a textbook designer's-deputy artifact. The risk is the word *"self-aware"*: anthropomorphic first-person construction claims ("fui construído com o SEJA e tenho consciência disso") are ungrounded and collide with "answer only from context." Narrow to **honest provenance disclosure**. |
| **Correctness / Grounding** | ⚠️ Adopt with guardrail | A rich taxonomy block in the prompt will be treated by the LLM as authoritative content — it will answer "o que é um plano SEJA?" from the *prompt* even with zero retrieved chunks, silently bypassing the not-found path. Keep the taxonomy strictly as an **interpretation lens** and re-assert the grounding contract **after** it. |
| **Architecture (T2)** | ⚠️ Adopt, but move the branch | Branching the prompt on `role == "admin"` *inside* `AnswerHelpWithRag` re-introduces an auth decision into the application layer (T2 violation). Thread a pre-resolved `meta_mode: bool` from the router, exactly like `roles` is already threaded. Use case stays a pure function of its inputs. |
| **Security** | ✅ Low risk | The real confidentiality boundary is the Chroma `where` filter (fail-closed) — a citizen physically cannot retrieve internal chunks, so the prompt cannot leak internal *content*. Admin-gating the full meta-mode is **UX-fit + tier coherence**, *not* a security control — don't bank security claims on it. Guardrail: meta-mode must not present the hard-excluded docs (security-checklists/threat-model) as describable. |
| **Privacy (C1)** | ✅ No new exposure | Static SEJA taxonomy is generic methodology text, not citizen PII; lives in-prompt, no new corpus. C1 untouched. |
| **UX** | ✅ Adopt | A light transparency line for all roles answers the user's "where does this come from?" question. The full SDLC framing would be noise for a citizen — correctly gated to admin. |

### The central tension — engaging demo vs. grounding guarantee

A more "aware" persona makes a better demo but pulls the deputy toward ungrounded first-person claims, which hollow out the grounding guarantee the whole bounded context was built to provide. **Resolution: you don't have to trade them.** The demo value comes from *honest provenance* — citations + `doc_type` labels + one transparency line — which is simultaneously on-message and grounded. Anthropomorphic "self-awareness" is the only place they actually conflict; drop that part and keep everything else.

---

## Recommendations (summary)

1. **[ALTA] Reframe "self-aware" → honest provenance disclosure.** Add one grounded transparency line for **all** roles, e.g. *"Minha base de conhecimento é a própria documentação de design da Fala-Gávea, e sempre cito as fontes."* This delivers the dogfooding core honestly for everyone. **Drop** any "fui construído com o SEJA e tenho consciência disso" identity/consciousness phrasing.

2. **[ALTA] Keep the grounding contract load-bearing and ordered last.** Insert the SEJA taxonomy as a labeled *interpretation guide* ("quando vir um doc do tipo `plan`, entenda que significa X"), then re-assert: *"responda sobre a plataforma APENAS com base em `<DOCUMENTOS>`; a taxonomia acima só ajuda a interpretar os trechos, não é fonte de fatos."* Add a test (mirrors Step 5 test (b)): taxonomy present + zero hits ⇒ still returns the not-found message and does not call the LLM.

3. **[ALTA / T2] Resolve the prompt variant in the router, not the use case.** Compute `meta_mode = current_user.role.value == "admin"` in `nl.py` (alongside `_ROLE_VISIBILITY`) and pass `execute(message, *, roles, meta_mode)`. Keep `AnswerHelpWithRag` a pure function of `(roles, meta_mode)`. Add a test asserting the meta block appears only when `meta_mode=True`.

4. **[MÉDIA] Admin meta-mode: taxonomy + SDLC framing yes; excluded docs no.** The augment may explain doc_types and the SEJA SDLC, but must **not** present security-checklists/threat-model as describable — they are hard-excluded from the corpus precisely so even an admin can't pull them through chat. Keep the prompt consistent with the index-time exclusion.

5. **[MÉDIA] Surface `doc_type` in the citations.** `cited_docs` already carries it in chunk metadata; add it to `CitedDoc`/`CitedDocResponse` (small Step 6 schema touch). This is the *grounded* way to make the assistant feel self-aware — the deputy shows its sources are the platform's own plans/research/design docs.

6. **[BAIXA] Scope is confirmed minimal — endorse.** Do **not** index `.claude/skills` into the corpus; **no** runtime skill execution / agentic tool-use (both explicitly rejected). Fold into plan-000177 **Step 5 + Step 6** (it now touches the schema + router, so not Step 5 alone) — no new plan needed.

## Trade-offs

- **SemEng demo richness × grounding guarantee** — resolved by getting demo value from honest provenance (citations + doc_type + transparency line), not anthropomorphic self-awareness.
- **UX coherence (admin-only meta-mode) × security framing** — keep the admin gate for UX-fit and tier legibility, but justify it as *coherence*, not *security*; the Chroma `where` filter remains the actual boundary.
- **T2 (auth-agnostic use case) × inline convenience** — thread a `meta_mode` flag from the router instead of branching on role inside the use case; small cost, preserves the trust boundary.

---

## Q&A log

**Q1 (2026-06-26):** following chat helper from plan 177, can we add SEJA skill into chat context to harness the chat itself?

**A1:** After clarifying that "SEJA skill" means **SEJA methodology/taxonomy in the helper's system prompt** (not RAG-indexing `.claude/skills`, not runtime skill invocation) and that the goal is a **self-aware / dogfooding demo** for the course: **yes, and it's a good, cheap, on-theme change.** It folds into plan-000177 Step 5 (+ a small Step 6 touch) rather than needing a new plan. Three guardrails make it safe and high-quality:
1. Reframe "self-aware" as **honest provenance disclosure** (one grounded transparency line for all roles; drop anthropomorphic construction claims) — this keeps it consistent with the project's committed metamessage ("AI as just another lens... assistance, not decision").
2. Keep the grounding contract **load-bearing and ordered after** the taxonomy block, so the taxonomy is an interpretation lens, not an answer source (defends the not-found path against hallucinated SDLC facts).
3. Resolve the role→prompt-variant branch (`meta_mode`) **in the router**, not inside the use case (T2). Admin-gate the full SEJA-taxonomy meta-mode for UX/coherence; surface `doc_type` in citations as the grounded way to make the deputy feel self-aware. Admin meta-mode must not present the hard-excluded sensitive docs as describable.

---

## Follow-up Q&A (2026-06-26)

**Q2:** plan 177 was implemented. update this research with this new info.

**A2:** Plan-000177 shipped, so the helper now exists in code and the five recommendations become **concrete edits to existing files** (not Step 5/6 plan amendments). Verified against the implementation:

- `src/fala_gavea/application/use_cases/help/answer_help_with_rag.py` — `_SYSTEM_PT_BR` (lines 8–15) is a single constant; `execute(self, message, *, roles)` (line 48) builds `system = _SYSTEM_PT_BR + <DOCUMENTOS>` (line 62); `CitedDoc` (lines 24–28) carries `source_path, section_title, score`.
- `src/fala_gavea/presentation/api/routers/nl.py` — `_ROLE_VISIBILITY` (lines 39–42) + `nl_help` (lines 80–101) already resolve `roles` in the router and map `CitedDoc → CitedDocResponse`.
- `src/fala_gavea/presentation/schemas/chat.py` — `CitedDocResponse` (the response field to extend).

Two recommendations are **already structurally satisfied** by the shipped code, which is good news:
- **Rec 3 (T2):** `roles` is already resolved in the router and passed in; `AnswerHelpWithRag` is already auth-agnostic. The `meta_mode` flag just extends the same pattern — no refactor of the boundary needed.
- **Rec 2 (grounding ordered last):** `execute()` returns `_NOT_FOUND_PT_BR` at lines 53–54 **before** the system prompt is assembled, so a taxonomy/meta block physically cannot bypass the not-found path. Adding the taxonomy keeps this property as long as it's appended to the prompt string, not to the retrieval gate.

### Concrete edit map (each rec → file/line)

| Rec | File | Edit |
|---|---|---|
| 1 — honest-provenance line (all roles) | `answer_help_with_rag.py:8–15` | Append one sentence to `_SYSTEM_PT_BR`, e.g. *"Minha base de conhecimento é a própria documentação de design da Fala-Gávea, e sempre cito as fontes."* No anthropomorphic "consciousness" phrasing. |
| 2 — taxonomy as lens, grounding last | `answer_help_with_rag.py:56–62` | Insert the taxonomy block as a labeled `<TAXONOMIA>` (interpretation guide), then re-assert *"responda APENAS com base em `<DOCUMENTOS>`; a taxonomia só ajuda a interpretar os trechos"* immediately before `<DOCUMENTOS>`. Add a regression test: meta/taxonomy present + zero hits ⇒ still returns `_NOT_FOUND_PT_BR`, no LLM call. |
| 3 — `meta_mode` in router | `answer_help_with_rag.py:48` + `nl.py:92–93` | Add `meta_mode: bool = False` to `execute(...)`; build a `_META_PT_BR` augment appended only when `meta_mode`. In `nl_help`: `meta_mode = current_user.role.value == "admin"`, pass `..., meta_mode=meta_mode)`. Keep the use case a pure function of `(roles, meta_mode)`. |
| 4 — admin meta-mode bounds | `answer_help_with_rag.py` (`_META_PT_BR` text) | The augment may explain doc_types/SDLC but must NOT name security-checklists/threat-model as describable (they are hard-excluded from the corpus). |
| 5 — `doc_type` in citations | `answer_help_with_rag.py:24–28,67–70` + `chat.py` (`CitedDocResponse`) + `nl.py:97–100` | Add `doc_type` to `CitedDoc` (from `hit.chunk.doc_type`), to `CitedDocResponse`, and map it in the router. `DocChunk.doc_type` already flows through retrieval. |

Net: a small, self-contained follow-up touching 3 files (+ tests), no architectural change, no new endpoint. Cleanly captured by **D-017**. Recommend a lightweight `/plan` (or direct implementation) scoped to exactly this edit map.

### Recommendations summary (follow-up)

1. **[ALTA]** Apply Rec 1 + Rec 2 + Rec 3 together as one prompt+router edit (`answer_help_with_rag.py` + `nl.py`), with the not-found regression test — the core of the dogfooding demo, grounded and T2-safe.
2. **[MÉDIA]** Apply Rec 5 (`doc_type` through `CitedDoc`/`CitedDocResponse`) — the grounded provenance signal in the UI.
3. **[MÉDIA]** Honor Rec 4 bounds in the `_META_PT_BR` copy (no excluded-doc mentions).
