# Research 000133 | REDESIGN-X | 2026-06-21 18:21 | NL to SQL for reports exploration

tags: nl-to-sql, query-ir, llm-reliability, security, data-pii, api-design

source: user request -- NL→SQL as an exploration/analysis alternative to plan-132's fixed query-params API
related: research-000129, research-000130, plan-000131, plan-000132

## User brief (verbatim)

> NL to SQL in the contexto of this project. folow research 129, 130, plan 131. Aqui pensando que NL para SQL é um problema resolvido. se temos controle total e informação neste projeto, NL para uma query SQL que roda diretamente no banco é uma poderosa ferramenta par analise e exploração. O plano 132 vai criar uma rota por onde passarao as queryes possíveis, que possuem um formato específico, porém não flexivel e poderoso suficiente para expressar o conjunto de possibilidades de um sql. Quais alternativas temos ?

## Agent interpretation

Plan-000132 ships `POST /reports/query` — a **structured query DSL** with a fixed Pydantic schema (multi-value `report_type_ids[]`/`urgencies[]`/`statuses[]`, `bbox`, date range, literal `text` LIKE, optional semantic `q` ranker, pagination). The user correctly observes this DSL has an **expressiveness ceiling**: it cannot express the aggregate/relational questions that real exploration needs — `GROUP BY` ("quantos relatos de alta urgência por tipo?"), time-bucketing ("relatos por semana"), joins to `forwardings` ("relatos encaminhados ao órgão X ainda pendentes"), `HAVING`, window functions. They propose **NL→SQL executed directly against the DB**, arguing that with full schema control NL→SQL is a "solved problem."

The question is **what alternatives exist** between (a) the rigid structured DSL and (b) full raw NL→SQL. This report maps the spectrum, weighs each option against the project's hard constraints, and recommends a concrete path.

## Files

- `_output/plans/plan-000132-unified-reports-query-api-phase-b.md` — the structured DSL under evaluation
- `_output/research-logs/research-000130-filter-assistant-nl-to-query-params.md` — prior NL→filter decision; the `format`+Pydantic+repair mitigation to reuse (F3)
- `product-design/project/constitution.md` — S3 (LLM read-only vs DB), C1 (local-only), T1/T2/T5 (boundary invariants)
- `src/fala_gavea/infrastructure/database/models.py` — the 5-table schema (note `users.email` + `users.password_hash` PII; `reports.text` PII)
- `src/fala_gavea/infrastructure/ollama/ollama_client.py` — local `qwen3:8b`; `format`-guided decoding pattern
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` — existing NL orchestration to mirror

---

## Findings

### F1 — Reframe: plan-132's API and NL→SQL are not competitors for the same slot

The premise "the query API should become NL→SQL" conflates two **different bounded contexts**:

- **Interactive filtering workspace** (plan-132's job): deterministic, row-returning, drives the map/table, must be *savable* (research-130 Phase C) and populate *editable chips* (research-130 Phase A). It needs a stable, typed contract — exactly a structured DSL.
- **Ad-hoc analytical exploration** (the gap the user names): open-ended aggregate questions that the fixed schema cannot express. This wants relational power.

These have opposite requirements. Forcing one endpoint to serve both either cripples analytics (the DSL ceiling) or pollutes the interactive layer with SQL-execution risk. **The answer is "complement," not "replace."** Keep plan-132 as the workspace foundation; add analytics as a *separate, clearly-labeled* capability if scope allows.

### F2 — "NL→SQL is a solved problem" does not hold for `qwen3:8b`

It is *approaching* solved for **frontier** models on **clean, well-documented** schemas with execution feedback. It is **not** solved for a local 8B model on the multi-table-join / `GROUP BY` / `HAVING` queries that motivate this request — which is precisely the hard part.

The user's own datapoint is the counter-argument: **GPT-4 reaches only ~54.9% execution accuracy on BIRD** (humans 92.96%) ([BIRD paper](https://arxiv.org/pdf/2305.03111)). On clean toy schemas (Spider) frontier models do well, but BIRD — real, messy, domain-specific — is the realistic analogue, and `qwen3:8b` lands well below GPT-4 there ([SLM-SQL](https://arxiv.org/pdf/2507.22478)). Generating *runnable* SQL is mostly solved; generating *correct* SQL that matches intent is not, and a weak model fails **silently** — plausible-looking SQL, wrong answer. For an analytics tool whose whole value is trustworthy numbers, silent-wrong is the worst failure mode.

Crucially, **"we have full control of the schema" cuts the other way**: full control means you can *constrain the model to a query IR it fills reliably* instead of asking it to author arbitrary SQL it gets wrong half the time.

### F3 — The real threat is the LLM as an untrusted query author over a PII-bearing schema

This is not classic SQL injection. The schema contains `users.password_hash`, `users.email`, and `reports.text` (citizen PII). Any path where the model emits SQL touching base tables can — via an innocent NL prompt, or a **prompt injection embedded in a report's text** that the model later reads — surface credential hashes or cross-correlate citizens. This violates the *spirit* of **S3** (LLM read-only vs DB) and the *letter* of least-PII-exposure. It rules out **option 3 (raw NL→SQL, direct execution)** outright for this project.

### F4 — Row-level security over arbitrary SQL is infeasible; over an IR or a view it is trivial

Enforcing "citizens see only their own reports" on raw user-authored SQL means rewriting arbitrary queries to inject `WHERE author_id = :uid` correctly across joins and subqueries — the exact class of problem that defeats hand-rolled SQL firewalls. Two moves make it disappear:

- **Scope the analytical tool to `agent`/`admin` only** (citizens never get it) via `require_role` in `dependencies.py` (T2). Agents/admins are already authorized to see all reports, so RLS largely evaporates.
- **Run everything over a curated PII-stripped VIEW** (`reports_analytics`) that *physically* excludes `users.email`/`password_hash` and excludes raw `reports.text` from selectable columns. Then "row-level security" reduces to "the view cannot see the sensitive data."

### F5 — A constrained **query IR** (option 5) beats guarded raw SQL (option 4) for this project

This is the central recommendation. Instead of the model emitting SQL, it emits a **constrained JSON query spec** that the backend compiles to parameterized SQLAlchemy:

```jsonc
// Example IR the model fills for "quantos relatos de alta urgência por tipo no último mês?"
{
  "dataset": "reports_analytics",          // allowlisted view only
  "dimensions": ["report_type_name"],      // allowlisted columns
  "measures": [{"agg": "count", "as": "n"}],
  "filters": [
    {"field": "urgency", "op": "in", "value": ["alta"]},
    {"field": "created_at", "op": "gte", "value": "2026-05-21"}
  ],
  "order_by": [{"field": "n", "dir": "desc"}],
  "limit": 50
}
```

Why the IR wins over guarded raw SQL:

| Dimension | Query IR (opt 5) | Guarded raw SQL (opt 4) |
|---|---|---|
| Mitigation reuse | **Reuses research-130's `format`+Pydantic+repair** — already proven for Phase A | New sqlglot AST allowlist parser to build and *maintain forever* |
| Allowlist nature | **Structural** — only expressible ops exist (safe by construction) | **Denylist arms race** — must stay ahead of every dangerous construct |
| Boundary (T5) | SQL never leaves the model; compilation happens in `infrastructure/` | LLM-authored SQL flows toward the DB — breaks T5's letter |
| Model demand | 8B reliably fills bounded JSON | 8B must author correct multi-table SQL (~the BIRD failure) |
| Security surface | Small, closed | Large, the project's biggest |

The IR recovers **most** of the missing expressiveness (group-by, aggregations, time-bucketing, a fixed set of bounded joins to `forwardings`/`report_types`). The genuine casualties are window functions and arbitrary `HAVING` — rare at hundreds of rows, and addable to the IR incrementally if a concrete need appears. This is the same lesson as research-130 F3: **the validated-structured-output contract IS the security control.** Raw SQL throws that contract away.

### F6 — If raw guarded SQL is nonetheless pursued, the minimum viable guardrail set

(Only if a stakeholder insists on true open-ended SQL — e.g., for a course "wow" demo. In rough order of necessity.)

1. **Read-only at the connection layer** — a separate SQLAlchemy engine with `PRAGMA query_only=ON` (and/or a read-only connection). This makes **S3 mechanically true**, not just by convention — the backstop everything else rests on.
2. **PII-stripped analytics VIEW as the only addressable surface** — no base tables, no `users` PII columns (F4).
3. **Role gate: `agent`/`admin` only** via `dependencies.py` (F4).
4. **sqlglot AST validation** — parse the generated SQL; assert exactly one statement, `SELECT`-only (reject DDL/DML/`ATTACH`/`PRAGMA`), and table/column allowlist. Regex is insufficient; parse the AST ([STELP](https://arxiv.org/pdf/2601.05467), [SQL assistant guardrails](https://exesolution.com/solutions/spring-boot-sql-assistant-guardrails-audit)).
5. **Forced `LIMIT` + statement timeout** — cheap insurance against pathological generated SQL (cross joins, missing LIMIT) even though data volume is tiny.
6. **One repair retry + graceful fallback** — mirror research-130; on unparseable/timeout return an empty result with "não consegui analisar," never a silent wrong answer.

Note that the IR (F5) makes #4 unnecessary and folds #2/#5 into its compiler — which is the point.

### F7 — Human-in-the-loop "show the SQL/spec" is mandatory regardless of path

For any NL→analytics path on an 8B model, the dominant UX failure is the *"Looks fine to me"* breakdown: a confident table backed by wrong SQL. The mitigation is the same transparency contract research-130 chose for filter chips: **render the generated SQL (or the IR spec, more readable for non-technical agents) and require an explicit "Run" gesture.** This turns "silent wrong query" into "user reviews and can reject," and gives the course project a strong communicability story (SIM/metacommunication).

### F8 — Scope reality check: this is a course project

Plan-132 plus research-130's semantic ranking + NL→filter **already deliver a defensible, demoable AI-assisted exploration story.** A full NL→analytics tool — even the IR version — is a substantial new subsystem (IR schema, compiler, view, prompt, draft/review UI, tests). Building **raw guarded SQL to "look powerful" is classic gold-plating** that adds the project's largest security surface for a feature a grader is unlikely to require. The highest-value sequencing: ship plan-132; **document the IR + view design as the future analytics path** (this report + a D-NNN entry); build the smallest IR only if course time allows.

---

## Recommendations summary

| # | Recommendation | Priority |
|---|----------------|----------|
| R1 | **Complement, do not replace.** Ship plan-132 as the deterministic foundation of the interactive filtering workspace. The expressiveness gap is real but belongs to a *separate* analytical capability, not to the filtering endpoint (two-tier hybrid, option 7). | HIGH |
| R2 | **Reject raw NL→SQL with direct execution (option 3).** It violates S3's spirit, exposes `users.password_hash`/`email` + `reports.text` PII (F3), breaks T5, and ships silently-wrong analytics on `qwen3:8b` (F2). The "solved problem" premise does not hold for a local 8B model on aggregate/join queries. | HIGH |
| R3 | **If analytics is built, use a constrained query IR (option 5), not guarded raw SQL (option 4).** LLM emits validated JSON (`format`+Pydantic+repair, reusing research-130 Phase A); backend compiles to parameterized SQLAlchemy in `infrastructure/`. Safe by construction, preserves T5, recovers group-by/aggregation/bounded-joins. | HIGH |
| R4 | **Scope to `agent`/`admin` only + run over a PII-stripped analytics VIEW.** Makes row-level security trivial (F4): citizens excluded via `require_role`; `users` PII and raw `reports.text` physically unreachable from the view. | HIGH |
| R5 | **Show-the-spec human-in-the-loop.** Render the generated SQL/IR and require an explicit Run gesture; on failure return empty + a clear note, never a silent wrong answer (F7). | MEDIUM |
| R6 | **Minimum viable guardrails if raw SQL is ever used anyway** (F6): read-only connection (`PRAGMA query_only`), PII-stripped view, role gate, sqlglot AST allowlist (single SELECT, table/column allowlist), forced LIMIT + timeout, one repair retry. | MEDIUM |
| R7 | **For the course timeline, defer or ship the smallest IR.** Plan-132 + research-130 already demo AI-assisted exploration. Record the IR/view design as the documented future analytics path; build only if time permits; never build raw guarded SQL for appearances (F8). | LOW |

**Considered & rejected:** (a) raw NL→SQL direct execution — PII/credential exposure + T5 violation + silent-wrong on 8B; (b) overloading `/reports/query` to accept SQL — conflates two contracts, breaks field-level authz; (c) guarded raw SQL as the *primary* analytics path — permanent allowlist-parser maintenance burden and larger surface than an IR for marginal extra power; (d) NL→ the plan-132 DSL as the analytics answer — inherits the very expressiveness ceiling being escaped.

---

## Q&A log

**Q1 (initial):** Plan-132 builds a fixed-format query API that cannot express the full power of SQL (aggregations, joins, group-by). NL→SQL running directly against the DB would be a powerful exploration/analysis tool, and with full schema control NL→SQL is arguably a solved problem. What alternatives do we have?

**A1:** Seven recommendations (R1–R7). The key reframe: plan-132's structured DSL and NL→SQL serve **different jobs** — the deterministic interactive filtering workspace vs. open-ended aggregate analysis — so the answer is **complement, not replace** (F1). The "solved problem" premise fails for the local `qwen3:8b`: GPT-4 itself only reaches ~55% execution accuracy on the realistic BIRD benchmark, and a small model fails *silently* on exactly the join/group-by queries being sought (F2). Raw NL→SQL is rejected because the LLM becomes an untrusted query author over a schema holding `users.password_hash`/`email` and PII-bearing `reports.text`, violating S3's spirit and T5 (F3). The recommended middle ground is a **constrained query IR** (option 5): the model emits validated JSON (reusing research-130's `format`+Pydantic+repair contract) that the backend compiles to parameterized SQLAlchemy — safe by construction, recovering most missing expressiveness, with no SQL leaving the model (F5). Make it **agent/admin-only over a PII-stripped analytics view** so row-level security becomes trivial (F4), add a **show-the-spec human-in-the-loop** (F7), and — given this is a course project — **document the IR design as a future path and build only the smallest version if time allows** (F8). A minimum-viable guardrail set is specified should raw SQL ever be pursued anyway (F6/R6).

## Sources

- [Can LLM Already Serve as A Database Interface? (BIRD) — arXiv](https://arxiv.org/pdf/2305.03111)
- [SLM-SQL: An Exploration of Small Language Models for Text-to-SQL — arXiv](https://arxiv.org/pdf/2507.22478)
- [Text-to-SQL Empowered by LLMs: A Benchmark Evaluation — arXiv](https://arxiv.org/pdf/2308.15363)
- [STELP: Secure Transpilation and Execution of LLM-Generated Programs — arXiv](https://arxiv.org/pdf/2601.05467)
- [SQL Assistant: Guardrails, Read-only Enforcement, and Audit Logs — exesolution](https://exesolution.com/solutions/spring-boot-sql-assistant-guardrails-audit)
- [Prompt injection is the new SQL injection — Cisco Blogs](https://blogs.cisco.com/ai/prompt-injection-is-the-new-sql-injection-and-guardrails-arent-enough)
- [LLM guardrails: Best practices — Datadog](https://www.datadoghq.com/blog/llm-guardrails-best-practices/)
