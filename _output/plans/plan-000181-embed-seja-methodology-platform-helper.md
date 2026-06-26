# DONE | 2026-06-26 17:02 UTC | Plan 000181 | FEATURE-NL | 2026-06-26 16:38 | Embed SEJA methodology into platform-helper (D-017) | Review: standard
plan_format_version: 1
source: research-000180 -- SEJA methodology in the platform-helper system prompt (dogfooding); refines D-014 via D-017

## Brief

source:research-000180 Embed SEJA methodology into the platform-helper (D-017): role-conditional system prompt in `AnswerHelpWithRag` with an honest-provenance line for **all** roles + an **admin-only** `meta_mode` SEJA-taxonomy/SDLC augment resolved in the `nl.py` router (T2); taxonomy as interpretation lens with the grounding contract re-asserted before `<DOCUMENTOS>` and the not-found path preserved; surface `doc_type` through `CitedDoc`/`CitedDocResponse` and the router citation mapping. No corpus/embedding changes, no new endpoint, no `.claude/skills` indexing, no runtime skill invocation.

## Agent Interpretation

Plan-000177 shipped the platform-helper (`POST /nl/help`, `AnswerHelpWithRag`, RAG over `falagavea_selfdocs`). Research-000180 (decision D-017) asks to make the helper **SEJA-aware** as a dogfooding demo — but through the **prompt layer only**, not the vector/retrieval layer. Concretely:

1. **Honest provenance, all roles** — add one grounded line to the base system prompt ("minha base de conhecimento é a própria documentação de design da Fala-Gávea, e sempre cito as fontes"). No anthropomorphic "I am conscious I was built with SEJA" claims (ungrounded; collides with the answer-only-from-context contract; off-message vs. the committed metamessage "a IA é só mais uma lente… assistência, não decisão").
2. **Admin-only meta-mode** — a `_META_PT_BR` augment carrying the SEJA `doc_type` taxonomy (plan/research/reflection/communication/design/journey/constitution/readme) + SDLC framing as an **interpretation lens**. Gated to admin via a `meta_mode` flag **resolved in the router** (T2: auth decisions live in the router/deps, not the use case). The use case stays a pure function of `(roles, meta_mode)`.
3. **Grounding preserved** — taxonomy is a lens, not a fact source. A re-assertion line ("responda APENAS com base em `<DOCUMENTOS>`; a taxonomia só ajuda a interpretar os trechos, não é fonte de fatos") is appended immediately before `<DOCUMENTOS>`. The not-found path already returns **before** the system prompt is assembled (`answer_help_with_rag.py:53-54`), so no meta/taxonomy text can bypass it — a regression test locks this in.
4. **`doc_type` in citations** — `DocChunk.doc_type` already flows out of `search()`; thread it through `CitedDoc` → `CitedDocResponse` → router mapping so the UI can show "Fonte: plano 000177" (the grounded provenance signal).

Security note (research-000180): admin-gating the meta-mode is **UX/tier coherence, not a security control** — the Chroma `where={"role_visibility": {"$in": roles}}` filter (`chroma_doc_search_client.py:81`, fail-closed) remains the real confidentiality boundary. `_META_PT_BR` must **not** name the hard-excluded docs (security-checklists/threat-model) as describable.

## Files

### Modified
- `src/fala_gavea/application/use_cases/help/answer_help_with_rag.py` -- honest-provenance line in `_SYSTEM_PT_BR`; new `_META_PT_BR` + `_GROUNDING_REASSERT_PT_BR`; `execute(..., meta_mode: bool = False)`; role-conditional prompt assembly; `doc_type` field on `CitedDoc`.
- `src/fala_gavea/presentation/schemas/chat.py` -- add `doc_type: str` to `CitedDocResponse`.
- `src/fala_gavea/presentation/api/routers/nl.py` -- resolve `meta_mode = current_user.role.value == "admin"`; pass to `.execute(...)`; map `doc_type` into `CitedDocResponse`.
- `tests/application/test_answer_help_with_rag.py` -- update `CitedDoc` equality (now carries `doc_type`); add meta_mode + not-found-with-meta tests.
- `tests/presentation/test_nl_help_router.py` -- assert `doc_type` present in `cited_docs`; assert admin path still 200 (meta-mode internal to prompt).
- `CLAUDE.md` -- one-line note that `/nl/help` admin responses include a SEJA-aware "meta" framing.

---

## Steps

### Step 1: Role-conditional SEJA-aware system prompt + doc_type on CitedDoc

Edit `src/fala_gavea/application/use_cases/help/answer_help_with_rag.py`.

1. **Base prompt (all roles)** — append one honest-provenance sentence to `_SYSTEM_PT_BR` (keep the existing "use APENAS os trechos… não invente" grounding):
   > "Minha base de conhecimento é a própria documentação de design da Fala-Gávea, e sempre cito as fontes."
   Do **not** add first-person "consciousness"/"fui construído com o SEJA e tenho consciência disso" phrasing.

2. **Admin meta augment** — add a module constant `_META_PT_BR` describing the SEJA `doc_type` taxonomy as an **interpretation lens** and the dogfooding/SDLC framing, e.g.:
   > "Esta plataforma foi construída com um processo de design assistido por IA (SEJA). Os trechos de documentação podem ser de vários tipos — `plan` (plano de implementação), `research` (investigação de design), `reflection` (reflexão), `communication` (material de comunicação), `design` (design do produto), `journey` (jornada de usuário), `constitution` (princípios), `readme`. Use esses tipos apenas para **interpretar** os trechos recuperados."
   It must **not** present security-checklists/threat-model (or any hard-excluded doc) as available/describable.

3. **Grounding re-assertion** — add a constant `_GROUNDING_REASSERT_PT_BR`:
   > "Responda sobre a plataforma APENAS com base nos trechos em `<DOCUMENTOS>`; a taxonomia acima só ajuda a interpretar os trechos, não é fonte de fatos."

4. **`execute` signature** — `execute(self, message: str, *, roles: list[str], meta_mode: bool = False) -> HelpAnswer`. Keep the early not-found return unchanged (before any system assembly). Assemble the prompt as: `parts = [_SYSTEM_PT_BR]`; if `meta_mode`, `parts.append(_META_PT_BR)`; `parts.append(_GROUNDING_REASSERT_PT_BR)`; `system = "\n\n".join(parts) + f"\n\n<DOCUMENTOS>\n{context_block}\n</DOCUMENTOS>"`.

5. **`doc_type` on citations** — add `doc_type: str` to the `CitedDoc` dataclass and populate it from `hit.chunk.doc_type` in the `cited` comprehension.

- **Files**: `src/fala_gavea/application/use_cases/help/answer_help_with_rag.py` (modify), `tests/application/test_answer_help_with_rag.py` (modify)
- **References**: `product-design/project/constitution.md` (T1, T2, C1), `product-design/project/product-design-as-coded.md` §4 (committed metamessage), `general/coding-standards.md`
- **Interface**: `AnswerHelpWithRag.execute(message, *, roles, meta_mode: bool = False) -> HelpAnswer`; `CitedDoc(source_path, section_title, score, doc_type)`
- **Verify**: `uv run pytest tests/ -k "answer_help"` passes; `uv run ruff check src/ tests/` clean; `uv run pyright src/` clean
- **Tests**: in `tests/application/test_answer_help_with_rag.py`: (a) update the existing `cited_docs` equality to include `doc_type="design"` (the `_chunk` helper already stamps `doc_type="design"`); (b) **meta_mode**: when `meta_mode=True` the system prompt contains the SEJA taxonomy marker (e.g. "SEJA") AND the grounding re-assertion; when `meta_mode=False` (default) it does **not** contain the taxonomy block but still answers; (c) **not-found-with-meta**: `execute(..., meta_mode=True)` with zero hits still returns `_NOT_FOUND_PT_BR` and `llm.call_count == 0` (meta cannot bypass grounding); (d) assert each cited doc exposes `doc_type`
- [x] Done

### Step 2: Router meta_mode resolution (T2) + doc_type through the schema

Wire the role→`meta_mode` decision in the router and thread `doc_type` to the response.

1. **`schemas/chat.py`** — add `doc_type: str` to `CitedDocResponse` (after `section_title`).
2. **`routers/nl.py`** `nl_help` — after resolving `roles`, add `meta_mode = current_user.role.value == "admin"` (only admin gets the SEJA meta framing; everyone gets the base honest-provenance prompt). Call `AnswerHelpWithRag(search_port, llm_client).execute(body.message, roles=roles, meta_mode=meta_mode)`. In the `CitedDocResponse(...)` mapping add `doc_type=c.doc_type`.

Keep auth resolution in the router only (T2) — the use case never inspects the role.

- **Files**: `src/fala_gavea/presentation/schemas/chat.py` (modify), `src/fala_gavea/presentation/api/routers/nl.py` (modify), `tests/presentation/test_nl_help_router.py` (modify), `CLAUDE.md` (modify)
- **Depends on**: Step 1
- **Interface**: `POST /nl/help` → `HelpChatResponse` whose `cited_docs[*]` now include `doc_type`; admin callers receive a SEJA-aware "meta" framing in the answer
- **Verify**: `uv run pytest tests/ -k "nl_help"` passes; `uv run ruff check src/ tests/` clean; manual: `POST /nl/help` as admin returns a SEJA-aware answer; as citizen returns the product answer; both include `doc_type` in citations
- **Tests**: in `tests/presentation/test_nl_help_router.py`: extend the `_RecordingSearchPort` chunk to a known `doc_type` and assert `body["cited_docs"][0]["doc_type"]` is present/correct in the citizen test; keep the admin test asserting 200 + `roles == ["public","internal"]` (meta-mode is internal to the prompt, not observable in the role mapping)
- **Docs**: add a one-line note to `CLAUDE.md` that admin `/nl/help` responses carry a SEJA-aware meta framing; post-skill syncs the `POST /nl/help` surface note in `product-design/project/product-design-as-coded.md`
- [x] Done

---

## Review

### Engineering perspectives

| Perspective | Status | Notes |
|---|---|---|
| P0 - Correctness | Adopted | Not-found path returns before prompt assembly (`answer_help_with_rag.py:53-54`); meta/taxonomy cannot bypass grounding — locked by Step 1 test (c). Grounding re-assertion ordered last, before `<DOCUMENTOS>`. |
| P0 - Security | Adopted | Admin-gating the meta-mode is UX/tier coherence, **not** a security control; the Chroma `where` role filter (fail-closed) remains the boundary. `_META_PT_BR` must not name hard-excluded docs. No new corpus, no `.claude/skills` indexing, no retrieval change. |
| P1 - Architecture (T2) | Adopted | `meta_mode` resolved in the router from the role; `AnswerHelpWithRag` stays a pure function of `(roles, meta_mode)` — auth never enters the application layer. Mirrors the existing `roles` threading. |
| P1 - Privacy (C1) | Adopted | Static SEJA taxonomy is generic methodology text, not citizen PII; lives in-prompt. No C1 surface change. |
| P2 - SemEng / Metacommunication | Adopted | Honest provenance (citations + `doc_type` + transparency line) delivers the dogfooding demo on-message with the committed metamessage; anthropomorphic "self-aware" phrasing explicitly excluded. |
| P2 - Testing | Adopted | Use case via fakes (meta_mode on/off, not-found-with-meta, doc_type); router via dependency overrides (doc_type in response). |
| P3 - UX | Adopted | Citizens get the product answer; admins get the SEJA framing — no SDLC lecture for citizens. `doc_type` shown as provenance. |
| P4 - Migration | N/A | No DB/schema migration; additive Pydantic field + prompt text. |

### Trade-offs

- **Honest provenance vs. anthropomorphic self-awareness**: chose honest provenance (grounded + on-message); dropped first-person "consciousness" claims that collide with the answer-only-from-context contract.
- **Admin-gated meta-mode vs. meta for all roles**: gated to admin for UX-fit and tier coherence; a citizen "o que é a Fala-Gávea?" should not get an SDLC lecture. Justified as coherence, not security.
- **Taxonomy in prompt vs. indexing `.claude/skills` into the corpus**: prompt-only keeps retrieval unchanged and avoids enlarging the citizen-readable corpus surface; the rejected RAG-content option was explicitly out of scope in research-000180.

---

## Test Plan

1. `uv run pytest tests/ -k "answer_help or nl_help"` → all green (incl. updated `doc_type` equality + new meta tests).
2. `POST /nl/help` as **citizen** ("o que é a Fala-Gávea?") → product answer, `cited_docs` carry `doc_type`, no SEJA/SDLC framing.
3. `POST /nl/help` as **admin** (same question) → SEJA-aware answer that can reference doc types/the development process, still grounded + cited.
4. Out-of-corpus question as admin → "não encontrei na documentação", `cited_docs == []`, no hallucinated SDLC facts (not-found path holds even with meta_mode on).
5. `uv run ruff check src/ tests/` and `uv run pyright src/` clean.

---

## Implementation Summary (2026-06-26, manual mode)

Both steps completed. 2 source files + 1 schema + 2 test files + CLAUDE.md.

- **Step 1 — `answer_help_with_rag.py`**: appended an honest-provenance line to `_SYSTEM_PT_BR` (all roles); added `_META_PT_BR` (admin SEJA-taxonomy lens, lists only safe doc types — no excluded docs) + `_GROUNDING_REASSERT_PT_BR`; `execute(..., meta_mode: bool = False)` assembles base → (meta + re-assertion only when `meta_mode`) → `<DOCUMENTOS>`; `doc_type` added to `CitedDoc` (from `hit.chunk.doc_type`). Refinement vs. plan: the grounding re-assertion is appended **only with the taxonomy** (the base prompt already grounds), avoiding a dangling "a taxonomia acima" reference when meta is off.
- **Step 2 — `nl.py` + `chat.py`**: `meta_mode = current_user.role.value == "admin"` resolved in the router (T2); passed to `.execute(...)`; `doc_type` added to `CitedDocResponse` and the citation mapping. CLAUDE.md note updated.

**Tests**: `tests/application/test_answer_help_with_rag.py` — updated `CitedDoc` equality (4 fields) + 3 new tests (meta-off omits SEJA; meta-on injects SEJA + re-assertion ordered before `</DOCUMENTOS>`; meta-on + zero hits still returns not-found without calling the LLM). `tests/presentation/test_nl_help_router.py` — asserts `doc_type` in the citizen response.

**Quality gate**: `pytest -k "answer_help or nl_help"` → 11 passed; full suite → **308 passed, 0 failures**; ruff + pyright clean on all touched files. Pre-existing repo-wide ruff errors (22, in untouched files e.g. `tests/test_parse_nl_filter.py`) left as-is — out of scope.

**Deferred / notes**: frontend `HelpChat.tsx` could surface `doc_type` per source ("Fonte: plano …") — scoped out of this plan (the API now exposes it; display-only enhancement). A reindex of `falagavea_selfdocs` is not required (no corpus/embedding change).

- [x] Step 1 — role-conditional SEJA-aware system prompt + doc_type on CitedDoc
- [x] Step 2 — router meta_mode (T2) + doc_type through the schema
