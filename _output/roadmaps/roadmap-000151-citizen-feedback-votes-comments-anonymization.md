# Roadmap 000151 | 2026-06-24 00:26 UTC | Citizen feedback: votes, comments, anonymization

source: research-000150

## Source
- `_output/research-logs/research-000150-citizen-feedback-votes-comments-anonymization.md` (research anchor)
- `product-design/project/product-design-as-coded.md` (entity hierarchy, permission model, UX patterns)
- `product-design/conventions.md` (directory layout, stack, conventions)

## Wave Summary

### Wave 0 — DB Foundation (sequential)
| # | ID | Title | Scope | Type | Plan | Status |
|---|-----|-------|-------|------|------|--------|
| 1 | db-migrations | Alembic migrations: votes, comments, anon tokens, nullable author_id | backend | technical | plan-000152 | done |

### Wave 1 — Backend (parallel, depends on Wave 0)
| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 2 | votes-backend | Vote entity + repo + use cases + API endpoints + rate limit | backend | feature | plan-000153 | db-migrations | done |
| 3 | comments-backend | Comment entity + repo + use cases + API endpoints | backend | feature | plan-000154 | db-migrations | done |
| 4 | anon-backend | AnonymousReportToken entity + repo + CreateReport + query path + geo coarsen | backend | feature | plan-000155 | db-migrations | done |

### Wave 2 — Frontend (parallel, depends on Wave 1)
| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 5 | votes-ux | Vote buttons UX on relato + forwarding cards | frontend | design | plan-000156 | votes-backend | pending |
| 6 | comments-ux | Comment section UX on forwarding detail | frontend | design | plan-000157 | comments-backend | pending |
| 7 | anon-ux | Anonymous toggle on report form + token storage + meus relatos | frontend | design | plan-000158 | anon-backend | pending |

> The `Plan` column entries are filled with real IDs reserved above. All 7 plans generated inline with this roadmap.

## Execution Instructions

### Wave 0 (sequential)
Execute first:
1. `/implement plan-000152` (db-migrations)

### Wave 1 (parallel — 3 plans)
All depend on Wave 0. Execute in parallel via multiple Claude Code sessions or worktree-isolated agents:
- `/implement plan-000153` (votes-backend)
- `/implement plan-000154` (comments-backend)
- `/implement plan-000155` (anon-backend)

### Wave 2 (parallel — 3 plans)
Depends on Wave 1. Execute after all Wave 1 plans complete:
- `/implement plan-000156` (votes-ux)
- `/implement plan-000157` (comments-ux)
- `/implement plan-000158` (anon-ux)
