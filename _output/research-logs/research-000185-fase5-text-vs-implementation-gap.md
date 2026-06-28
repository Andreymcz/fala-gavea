# Research 000185 | fala-gavea | 2026-06-28 12:37 UTC | Fase 5 text vs implementation gap
tags: documentation, accuracy, ai-curation, semantic-search, forwardings

## User brief

> o quanto que o que está implementado difere deste texto: [LaTeX `\subsection{Fase 5 — Novo fala-gávea: Canal comunitário com Busca inteligente}` com TODO "REVISAR, tem coisas que são ideais mas n implementadas na pratica"]

## Agent interpretation

The user is writing an academic final report (Fase 5 subsection) and flagged with a `TODO` that the paragraph mixes **idealized design** with **what was actually built**. The task is a factual gap audit: claim-by-claim, mark each assertion in the text as **implemented**, **partial/overstated**, or **aspirational (not built)**, with code evidence — so the user can rewrite the paragraph to match reality (or split intent from delivery).

This is a verification/audit question, not a design trade-off, so the multi-perspective reviewer pass is not applicable; the analysis is grounded directly in `src/` and the as-coded design doc.

## Files inspected

- `product-design/project/product-design-as-coded.md` (full as-coded state)
- `src/fala_gavea/application/use_cases/nl/parse_nl_filter.py`
- `src/fala_gavea/infrastructure/llm/llm_filter_parser.py`
- `src/fala_gavea/application/use_cases/forwardings/create_forwarding.py`
- `src/fala_gavea/domain/entities/` (entity inventory)
- Repo-wide greps: `curation|curadoria|few-shot|correction|suggest|categor|classif|event`

---

## Verdict

The text is **accurate about the platform's structure** (loop cidadão↔agente, mapa colaborativo, encaminhamentos, transparência, busca semântica) but **describes a central feature that does not exist in code**: the *feedback loop where agent corrections to AI categorizations become curation events that feed few-shot learning*. That entire mechanism — and the AI categorization it presupposes — is **unimplemented**. The flagship busca-inteligente example also overstates one dimension (geographic/bairro filtering).

The TODO instinct is correct. Roughly one paragraph (the design-hypothesis core) is aspirational.

---

## Claim-by-claim analysis

### ✅ Accurate — implemented

| Claim in text | Evidence |
|---|---|
| Loop cidadão → agente → cidadão; reúne coleta + mapa + clusterização + encaminhamento numa solução centralizada | WorkspacePage SPA + REST API; journeys JM-TB-001/002/003 implemented end-to-end (as-coded §8). |
| Cidadão registra relatos georreferenciados que integram um mapa colaborativo | `POST /reports` (lat/lon/urgency/type), MapView clustered (react-leaflet-cluster), `GET /reports/geojson` (as-coded §1, §8). |
| Agentes triam/agrupam e **criam encaminhamentos institucionais — associando vários relatos a um único órgão, com status e solução proposta** | `CreateForwarding` links N reports → 1 `institution` + `proposed_solution` + `status` (aguardando_solucao/solucao_em_andamento/finalizado), many-to-many via `ForwardingReport`. This sentence is implemented essentially verbatim. |
| Cidadão acompanha o processo de forma transparente (registro → resolução) | `GET /forwardings/public`, `GET /forwardings/public/{id}`, `GET /reports/{id}/forwardings`, `GET /forwardings/mine`, anonymous-claim token (`GET /reports/mine?anonymous_token=`); PublicForwardingsPage (as-coded §1, §4, §8). |
| Agente explora a base por **busca semântica** e recebe **sugestões de relatos similares** | `GET /reports/search`, `GET /reports/{id}/similar`, `POST /reports/similar-to-set` (basket open-similars), SimilarsView (as-coded §3). |
| IA atua como **auxiliar da curadoria, não curador principal** (humano no comando) | Strong fit: NL filter **never auto-applies** — user must click "Aplicar sugestão ao rascunho"; RAG chat always cites `cited_report_ids`; AiBadge provenance markers (as-coded §8, Metacomm §4). |

### 🟡 Partial / overstated

| Claim in text | Reality |
|---|---|
| **Busca inteligente**: agente "expressa em linguagem natural a intenção de exploração e o sistema traduz essa intenção em consultas e recortes" | Implemented as `POST /nl/filter` → `LLMFilterParser` → `ParseNLFilter`. Real, but the translatable dimensions are **only** `report_type_ids, urgencies, statuses, since, until, text, q` (`_ALLOWED_KEYS` in `parse_nl_filter.py`). |
| Example: *"relatos de iluminação na Rocinha nos últimos trinta dias"* | "iluminação" → `text`/`q` ✅; "últimos trinta dias" → `since` ✅; **"na Rocinha" (bairro/localização) is NOT a supported filter** — there is no geographic/bairro/bbox dimension in the NL parser (`bbox` is intentionally excluded). The location phrase would, at best, leak into free-text `text`. The flagship example promises geographic NL filtering that doesn't exist. (`Rocinha` is also outside Gávea — fine as illustration, but the geo recorte is the unimplemented part.) |

### ❌ Aspirational — NOT implemented (the TODO core)

| Claim in text | Reality |
|---|---|
| Agente "recebe **sugestões de categorização**" | **No AI categorization anywhere.** `report_type` is chosen manually by the citizen at creation. The AI surface is: semantic search, similar reports, TF-IDF keyword clusters, RAG chat, NL→filter. None of these suggests a category for a report. **Note:** an AI report_type-suggestion feature was explicitly researched (research-000172, research-000170) and planned (plan-000174 — `SuggestReportType` via ChromaDB, nullable `report_type_id`, `PATCH /reports/{id}/report-type`, `ai_source` provenance), but **never implemented** — `report_types/` has only create/update/delete/bulk use cases; no suggest use case, no PATCH endpoint exists. So this is a *known, deliberately-deferred* gap, not an oversight. |
| "as **correções que o agente fazia às categorizações sugeridas pela IA** eram descartadas, desperdiçando supervisão humana" | The premise has no referent: there is no AI categorization to correct, and **agents cannot even edit a report's category** — there is no `PATCH /reports/{id}`; reports are immutable after creation except `status` (auto-set to `encaminhado` on forwarding). So no corrections are happening, let alone being discarded. |
| "Cada correção de categoria feita pelo agente é registrada como um **evento de curadoria**" | **No curation-event entity, table, or recording exists.** Entity inventory: `user, report, report_type, forwarding, forwarding_report, comment, vote, saved_filter, anonymous_report_token` — nothing for curation events. `CreateForwarding` records nothing about categories. |
| "...que passa a **alimentar as sugestões futuras da IA**" — via **few-shot** (não fine-tuning), barato, auditável | **No few-shot learning loop.** No prompt-example store, no correction corpus, no mechanism feeding past corrections into any LLM call. `BERTopic` exists but is **dormant** (never instantiated; reserved for "future fine-tuning" per as-coded §3). |

The bold middle of the paragraph — "A análise de uso revelou… as correções… eram descartadas… A hipótese de design resultante foi que essas correções deveriam realimentar o sistema… por few-shot…" — describes a **design hypothesis / future direction**, presented in past tense as if shipped. It is the single biggest divergence.

---

## Recommendations

1. **(Medium) Rewrite the categorization-feedback paragraph to separate intent from delivery.** Move the few-shot curation loop, "sugestões de categorização", "correções descartadas" and "evento de curadoria" into an explicit *design hypothesis / trabalho futuro* framing (conditional/future tense), OR clearly label the section as "design idealizado" vs "protótipo entregue". As written, it claims a delivered feature that has no code.
2. **(Medium) Fix the busca-inteligente example** so it doesn't promise geographic/bairro filtering. Either drop "na Rocinha" or replace with a dimension the parser supports (tipo, urgência, status, janela temporal, busca semântica/textual) — e.g. *"relatos de iluminação com urgência alta nos últimos trinta dias"*.
3. **(Low) Keep the accurate spine as-is.** The loop cidadão↔agente, mapa colaborativo, encaminhamento multi-relato→órgão com status/solução, transparência ao cidadão, busca semântica + similares, and "IA como auxiliar com humano no comando / nunca auto-aplica" are all faithfully implemented and well-supported.
4. **(Optional, if the text must stay as written) Implement a minimal slice** to make the claim true: (a) an AI category suggestion at triage, (b) a `CurationEvent` record when the suggestion is overridden, (c) inject recent overrides as few-shot examples into the suggestion prompt. This is a real feature, not a doc edit — out of scope for "polishing stage" per recent project direction.

## Q&A log

**Q1 (initial):** o quanto que o que está implementado difere deste texto da Fase 5?

**A1:** O texto acerta a estrutura da plataforma (loop cidadão↔agente, mapa colaborativo, encaminhamento multi-relato→órgão com status/solução, transparência, busca semântica + similares, IA como auxiliar que nunca auto-aplica — todos implementados). Diverge em dois pontos, sendo um grave: (1) **grave** — todo o mecanismo central de "sugestões de categorização pela IA → correções do agente → evento de curadoria → few-shot que realimenta a IA" **não existe no código**: não há sugestão de categoria, não há sequer edição de categoria pelo agente (`report` é imutável fora do `status`), não há entidade/registro de evento de curadoria, e não há loop de few-shot (BERTopic está dormente). Esse parágrafo descreve uma hipótese de design/trabalho futuro em tempo passado, como se entregue. (2) **menor** — o exemplo "relatos de iluminação na Rocinha nos últimos trinta dias" promete filtro geográfico por bairro que o parser de NL não suporta (campos permitidos: tipo, urgência, status, datas, texto, busca semântica; sem dimensão geográfica). Recomendo reescrever o parágrafo de categorização como "trabalho futuro/hipótese" e corrigir o exemplo da busca.

## Recommendations summary

- **Medium** — Reframe the few-shot curation-feedback loop (sugestões de categorização, correções descartadas, evento de curadoria, few-shot) as design hypothesis / future work; it has no implementation.
- **Medium** — Correct the busca-inteligente example to avoid promising geographic/bairro NL filtering, which `_ALLOWED_KEYS` does not support.
- **Low** — Retain the accurate structural spine (loop, mapa, encaminhamentos, transparência, busca semântica + similares, IA-auxiliar) unchanged.
- **Optional** — If the claim must stay, implement AI category suggestion + `CurationEvent` capture + few-shot injection (a real feature, outside the current polishing stage).
