# Check 000143 | REVIEWplan-000140 | 2026-06-22 12:10 UTC | Code Review: NL filter parser + NL assistant UX

## Scope: plan-000140 changes (HEAD~5..HEAD)

## Perspective Evaluation

| Perspective | Status | Summary |
|-------------|--------|---------|
| SEC | Deferred | IP-based rate limiter ineffective behind proxy; non-thread-safe singleton; error detail leaks |
| API | Deferred | No Retry-After headers on 429; error detail forwarded to client |
| ARCH | Adopted | Clean layer boundaries respected throughout |
| TEST | Deferred | LLMFilterParser retry path untested; frontend error-path test pattern is fragile |
| PERF | Deferred | Sync LLM call blocks thread pool up to 16s under retry |

## Issues

| Severity | Perspective | Description | File:Line | Resolution |
|----------|-------------|-------------|-----------|------------|
| HIGH | SEC | Rate limiter keyed on IP only, ineffective behind reverse proxy | main.py:711, nl.py:761 | Advisory — local dev scope |
| HIGH | SEC | Singleton `_filter_parser_instance` not thread-safe | dependencies.py:145-155 | Advisory — pre-existing pattern |
| MEDIUM | SEC | ParseError.message echoed to HTTP response detail | routers/nl.py:787-796 | Advisory |
| MEDIUM | API | No Retry-After header on 429 responses | routers/nl.py | Advisory |
| MEDIUM | PERF | Sync LLM call blocks thread pool up to 16s | routers/nl.py:776 | Advisory — local dev scale |
| MEDIUM | TEST | LLMFilterParser retry path has no unit tests | llm_filter_parser.py | Advisory — out of plan scope |
| LOW | TEST | Frontend error-path tests use fragile manual reject ref | FilterPanel.test.tsx:209-251 | Advisory — tests pass |
| LOW | ARCH | Use case imported presentation schema | parse_nl_filter.py:4 | **FIXED** — removed import |

## Generator-Critic Iterations
- Iteration count: 0/2
- Findings per iteration: [0 critical after arch fix]
- Resolution status: 1 critical (ARCH) resolved inline; all remaining findings advisory

## Overall

**APPROVED with advisory findings.** 7 advisory findings logged for future improvement. 1 critical arch violation (use case importing presentation schema) fixed inline before commit.
