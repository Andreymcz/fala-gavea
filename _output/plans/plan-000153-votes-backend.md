# Plan 000153 | feat/votes-backend | 2026-06-24 00:26 UTC | Vote feature backend: use cases, endpoints, rate limit | Review: standard
plan_format_version: 1

source: roadmap-000151

## Brief

Implement the vote feature backend: SQLAlchemy repository, use cases (CastVote, RetractVote, GetVoteSummary), API endpoints (POST/DELETE /reports/{id}/votes, POST/DELETE /forwardings/{id}/votes), response schema enrichment (VoteSummary added to relevant responses), and per-user rate limiting via slowapi.

## Context

Domain entities and ABCs are defined in plan-000152. This plan implements the infrastructure and API layers. Votes apply to both `report` and `forwarding` targets via a generic `target_type + target_id` model. Self-voting is blocked at the use-case layer.

Permission model:
- Any authenticated user can cast/retract votes
- Unauthenticated callers see aggregated vote counts in public endpoints (no `user_vote` field)

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Self-vote block | Use-case layer, not DB | Cleaner domain boundary; DB constraint would require joining across tables |
| Upsert behavior | UPSERT (update value if vote exists) | Changing +1 to -1 is a natural user action; separate retract endpoint handles removal |
| Rate limit | 20 vote operations/min per user via slowapi | Same pattern as POST /nl/filter; deters scripted farming without infrastructure overhead |
| VoteSummary in existing responses | Added to `ReportResponse` and `PublicForwardingResponse` schemas | Avoids extra round-trips; vote context arrives with the entity |
| Unauthenticated VoteSummary | `user_vote: null` in public responses | Public callers see counts but cannot vote |

## Steps

### Step 1: SQLAlchemy vote repository

Implement `SQLAlchemyVoteRepository` in `src/fala_gavea/infrastructure/repositories/vote_repository.py`:

- `cast(vote: Vote) -> Vote`: INSERT OR REPLACE using `vote.value` (upsert on unique constraint). Raises `SelfVoteError` if resolved by use case before reaching repo (repo trusts use case).
- `retract(voter_id, target_type, target_id) -> None`: DELETE WHERE; no-op if absent.
- `get_summary(target_type, target_id, voter_id: str | None) -> VoteSummary`: COUNT WHERE value=1 and value=-1 in two subqueries; also fetch caller's own vote value if `voter_id` provided.

Register `get_vote_repo()` dependency in `presentation/api/dependencies.py` (returns `SQLAlchemyVoteRepository`).

- **Files**: `src/fala_gavea/infrastructure/repositories/vote_repository.py` (create), `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **Tests**: `tests/integration/test_vote_repository.py` — test cast, retract, get_summary, duplicate vote upsert
- [ ] Done

### Step 2: Use cases

Implement in `src/fala_gavea/application/use_cases/votes/`:

- `cast_vote.py` — `CastVoteUseCase.execute(voter_id, target_type, target_id, value)`: validates `target_type in ('report', 'forwarding')`; validates `value in (1, -1)`; resolves target author via `IReportRepository` or `IForwardingRepository`; raises `SelfVoteError` if `voter_id == target_author_id`; delegates to `IVoteRepository.cast()`.
- `retract_vote.py` — `RetractVoteUseCase.execute(voter_id, target_type, target_id)`: delegates to `IVoteRepository.retract()`.
- `get_vote_summary.py` — `GetVoteSummaryUseCase.execute(target_type, target_id, voter_id)` → `VoteSummary`.

Add `SelfVoteError` to `domain/exceptions.py`.

- **Files**: `src/fala_gavea/application/use_cases/votes/cast_vote.py` (create), `src/fala_gavea/application/use_cases/votes/retract_vote.py` (create), `src/fala_gavea/application/use_cases/votes/get_vote_summary.py` (create), `src/fala_gavea/domain/exceptions.py` (modify)
- **Tests**: `tests/unit/use_cases/test_cast_vote.py` — test self-vote rejection, valid cast, invalid target_type, invalid value
- [ ] Done

### Step 3: Request/response schemas

Add to `src/fala_gavea/presentation/schemas/`:

```python
class VoteSummarySchema(BaseModel):
    upvotes: int
    downvotes: int
    user_vote: int | None  # +1, -1, or null

class CastVoteRequest(BaseModel):
    value: int  # must be 1 or -1
```

Add `votes: VoteSummarySchema | None = None` to `ReportResponse` and `PublicForwardingResponse`. This field is populated when the endpoint enriches the response; it is `None` when the endpoint doesn't include it (e.g., list endpoints that don't yet enrich votes).

- **Files**: `src/fala_gavea/presentation/schemas/votes.py` (create), `src/fala_gavea/presentation/schemas/reports.py` (modify), `src/fala_gavea/presentation/schemas/forwardings.py` (modify)
- **Tests**: N/A (schema validation tested implicitly via endpoint tests)
- [ ] Done

### Step 4: API endpoints

Add `src/fala_gavea/presentation/api/routers/votes.py` with four endpoints:

```
POST   /reports/{report_id}/votes         → any authenticated user; body: CastVoteRequest; returns VoteSummarySchema
DELETE /reports/{report_id}/votes         → any authenticated user; returns 204
POST   /forwardings/{forwarding_id}/votes → any authenticated user; body: CastVoteRequest; returns VoteSummarySchema
DELETE /forwardings/{forwarding_id}/votes → any authenticated user; returns 204
```

Apply slowapi rate limit `20/minute` per user (keyed on `current_user.id`) to all four endpoints. Return 404 if the target entity does not exist. Return 409 + `SelfVoteError` message if the caller tries to vote on their own entity. On `POST`: call `CastVoteUseCase` then `GetVoteSummaryUseCase` and return the updated summary. On `DELETE`: call `RetractVoteUseCase` and return 204.

Mount `votes_router` in `presentation/api/main.py`.

- **Files**: `src/fala_gavea/presentation/api/routers/votes.py` (create), `src/fala_gavea/presentation/api/main.py` (modify)
- **Verify**: POST /reports/{id}/votes with value=1 returns `{upvotes:1, downvotes:0, user_vote:1}`; second POST with value=-1 upserts to `{upvotes:0, downvotes:1, user_vote:-1}`; DELETE returns 204; self-vote returns 409
- **Tests**: `tests/integration/test_votes_api.py`
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000153 (votes-backend)
