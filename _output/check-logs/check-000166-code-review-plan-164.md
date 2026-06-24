# Check 000166 | REVIEW staged | 2026-06-24 18:36 UTC | Code Review: plan-000164 votes UX fix

## Scope
Staged changes from plan-000164: votes API fix, Meus relatos nav, inline votes in table/map.

## Perspective Evaluation

| Perspective | Status | Notes |
|-------------|--------|-------|
| Security (SEC) | Adopted | Fixed: get_optional_user now catches only InvalidCredentialsError |
| Performance (PERF) | Deferred | Sort-on-upvotes races async batch fetch — advisory only |
| API Design | Adopted | Endpoints correctly registered; batch capped at 200 IDs |
| Architecture | Adopted | Clean architecture conventions followed |

## Issues Found and Resolved

| # | Severity | Finding | Resolution |
|---|----------|---------|------------|
| 1 | MEDIUM | `get_optional_user` caught all exceptions, masking token abuse | Fixed: narrowed to `InvalidCredentialsError` only |
| 2 | MEDIUM | Sort by upvotes races async batch fetch (advisory) | Deferred — cosmetic race on initial render |
| 3 | MEDIUM | `meus_relatos` effect may miss if auth not yet hydrated | Deferred — nav link only visible when user is truthy |
| 4 | LOW | Batch endpoint had no upper bound on IDs | Fixed: added 200-ID cap with 422 response |
| 5 | LOW | Dialog VoteButtons used `disabled` (hides) vs row `readOnly` (shows) | Fixed: aligned dialog to `readOnly` |

## Overall: PASS (no HIGH severity issues; all MEDIUM/LOW resolved or deferred)
