# Plan 000154 | feat/comments-backend | 2026-06-24 00:26 UTC | Comment feature backend: use cases and endpoints | Review: light
plan_format_version: 1

source: roadmap-000151

## Brief

Implement the comment feature backend: SQLAlchemy repository, use cases (AddComment, DeleteComment, ListComments), and API endpoints (GET/POST /forwardings/{id}/comments, DELETE /forwardings/{id}/comments/{comment_id}). Comments are flat (no threading) and moderation is delete-only via owner or agent/admin.

## Context

Domain entity `Comment` and `ICommentRepository` ABC defined in plan-000152. This plan covers the infrastructure and presentation layers. Comments belong to `forwardings`, not to individual reports. The use case is: citizens and agents can add comments to a forwarding (public thread), and the comment owner or any agent/admin can delete a comment.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Comment visibility | Public read (GET unauthenticated) | Transparency: anyone can read the thread on a forwarding |
| Comment authorship | Any authenticated user | Citizens can express concern; agents can provide updates |
| Delete authorization | Owner (author_id == current_user.id) OR agent+admin | Agents moderate; citizens can retract their own |
| Text length | 1–500 chars | Enough for a comment; not a discussion forum |
| Threading | None (flat) | PoC scope; self-referential FK adds complexity not warranted |
| Ordering | `created_at ASC` (oldest first) | Natural chronological thread reading |

## Steps

### Step 1: SQLAlchemy comment repository

Implement `SQLAlchemyCommentRepository` in `src/fala_gavea/infrastructure/repositories/comment_repository.py`:

- `add(comment: Comment) -> Comment`: INSERT and return with generated id/created_at
- `delete(comment_id: str) -> None`: DELETE WHERE id=; no-op if absent
- `find_by_id(comment_id: str) -> Comment | None`: for authorization check in delete
- `list_by_forwarding(forwarding_id: str) -> list[Comment]`: SELECT WHERE forwarding_id=, ORDER BY created_at ASC

Register `get_comment_repo()` in `presentation/api/dependencies.py`.

- **Files**: `src/fala_gavea/infrastructure/repositories/comment_repository.py` (create), `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **Tests**: `tests/integration/test_comment_repository.py`
- [ ] Done

### Step 2: Use cases

Implement in `src/fala_gavea/application/use_cases/comments/`:

- `add_comment.py` — `AddCommentUseCase.execute(forwarding_id, author_id, text)`: validates forwarding exists via `IForwardingRepository`; validates `len(text.strip()) in [1, 500]`; creates and saves `Comment`.
- `delete_comment.py` — `DeleteCommentUseCase.execute(comment_id, requestor_id, requestor_role)`: fetches comment; raises `NotFoundError` if absent; raises `PermissionError` if `requestor_id != comment.author_id` AND `requestor_role not in ('agent','admin')`; calls `ICommentRepository.delete()`.
- `list_comments.py` — `ListCommentsUseCase.execute(forwarding_id)` → `list[Comment]`.

- **Files**: `src/fala_gavea/application/use_cases/comments/add_comment.py` (create), `src/fala_gavea/application/use_cases/comments/delete_comment.py` (create), `src/fala_gavea/application/use_cases/comments/list_comments.py` (create)
- **Tests**: `tests/unit/use_cases/test_comments.py`
- [ ] Done

### Step 3: Schemas and API endpoints

Add `CommentResponse(id, forwarding_id, author_id, text, created_at)` and `AddCommentRequest(text: str)` to `presentation/schemas/comments.py`.

Add `src/fala_gavea/presentation/api/routers/comments.py`:

```
GET    /forwardings/{forwarding_id}/comments              → public; returns list[CommentResponse]
POST   /forwardings/{forwarding_id}/comments              → any authenticated user; returns CommentResponse (201)
DELETE /forwardings/{forwarding_id}/comments/{comment_id} → owner or agent+admin; returns 204
```

Mount `comments_router` in `main.py`. Return 404 if the forwarding does not exist (GET/POST). Return 403 if delete authorization fails.

- **Files**: `src/fala_gavea/presentation/schemas/comments.py` (create), `src/fala_gavea/presentation/api/routers/comments.py` (create), `src/fala_gavea/presentation/api/main.py` (modify)
- **Verify**: POST /forwardings/{id}/comments returns 201 with comment; GET returns the list; DELETE by owner returns 204; DELETE by other citizen returns 403; DELETE by agent returns 204
- **Tests**: `tests/integration/test_comments_api.py`
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000154 (comments-backend)
