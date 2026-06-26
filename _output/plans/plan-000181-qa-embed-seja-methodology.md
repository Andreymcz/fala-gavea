# QA Log — plan-000181 | Embed SEJA methodology into platform-helper (D-017)

source: plan-000181 | follows research-000180 / D-017

## Brief

> following chat helper from plan 177, can we add SEJA skill into chat context to harness the chat itself? → (clarified) embed SEJA **methodology/taxonomy in the system prompt** for a **self-aware/dogfooding demo**; then: "plan needed changes".

## Q&A

**Q1:** Can we add "SEJA skill" into the help-chat context to harness the chat itself?

**A1:** Clarified via AskUserQuestion to mean **methodology in the system prompt** (not RAG-indexing `.claude/skills`, not runtime skill invocation) for a **self-aware/dogfooding** demo. Researched as research-000180 → decision D-017. The platform-helper (plan-000177) already RAG-indexes SEJA's *products* (plans/research/communication) as vectors; this change adds SEJA's *methodology* at the prompt layer only.

**Q2:** How will SEJA be embedded into this help RAG engine?

**A2:** Two distinct channels: (A) SEJA's **products** are already vector-embedded into the `falagavea_selfdocs` Chroma collection via `walk_corpus`/`reindex_all` (`chroma_doc_search_client.py`); (B) SEJA's **methodology/taxonomy** is **not** embedded — it enters as static text in the system prompt (`_SYSTEM_PT_BR` / admin `_META_PT_BR`), acting as an interpretation lens over the `doc_type` metadata that Channel A stamps on each chunk. The `doc_type` field is the bridge between the two; the role-visibility `where` filter keeps Channel A role-scoped.

**Q3:** Plan the needed changes.

**A3:** Generated plan-000181 (Review: standard, inheriting research-000180's perspective review). Two additive steps: (1) `AnswerHelpWithRag` — honest-provenance line (all roles), admin-only `_META_PT_BR` SEJA-taxonomy lens, `_GROUNDING_REASSERT_PT_BR` ordered last, `execute(..., meta_mode)`, `doc_type` on `CitedDoc`; (2) router `nl.py` resolves `meta_mode = role == "admin"` (T2) + threads `doc_type` through `CitedDocResponse`. Guardrails: admin-gating is coherence not security (Chroma `where` filter remains the boundary); `_META_PT_BR` must not name hard-excluded docs; not-found path preserved (regression test).

## Notes

- Concurrent signal: project entering **polishing stage** (no new features). This plan is a *refinement* of approved decision D-017, consistent with polishing, but implementation may be deferred until after the polish pass at the user's discretion.
