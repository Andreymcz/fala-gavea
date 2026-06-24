# Plan 000152 | feat/db-schema | 2026-06-24 00:26 UTC | DB schema: votes, comments, anon tokens, nullable author_id (wipe & recreate) | Review: light
plan_format_version: 1

source: roadmap-000151

## Brief

Add all schema changes required by the citizen feedback + anonymization features by updating the SQLAlchemy models and wiping + recreating the DB. No Alembic migration needed — the DB will be wiped and seeded fresh. Changes: nullable `author_id` on `reports`, three new tables (`votes`, `comments`, `anonymous_report_tokens`), and six new domain entities + repository ABCs.

## Context

Wave 1 backend plans all depend on these schema changes and domain stubs being present. By wiping and recreating the DB, we avoid Alembic migration complexity on SQLite (which doesn't support ALTER COLUMN without table recreation). Seed scripts will be re-run after Wave 2 to restore dev data.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Migration strategy | Wipe DB + recreate via `create_all()` | Simpler than Alembic ALTER on SQLite; acceptable for a PoC where seed scripts can restore dev data |
| `author_id` nullability | `nullable=True` (was implicitly NOT NULL) | Required for anonymous reports |
| Vote target | `target_type TEXT + target_id TEXT` (generic) | Allows voting on reports and forwardings without separate join tables |
| Vote value | `Integer CHECK(value IN (1, -1))` | Simple +1/-1 |
| Comments | FK to `forwardings.id` with CASCADE DELETE | Comments belong to forwardings only |
| AnonymousReportToken | Separate table from Report | Keeps Report entity clean; independent lifecycle |
| `token_hash` | SHA-256 hex; plaintext never stored | DB leak does not expose claim tokens |

## Steps

### Step 1: Domain entity dataclasses + repository ABCs

Add three new domain entities and three repository ABCs:

**Entities** (pure Python dataclasses, no DB dependencies):
- `src/fala_gavea/domain/entities/vote.py`:
  ```python
  @dataclass
  class VoteSummary:
      upvotes: int
      downvotes: int
      user_vote: int | None  # +1, -1, or None

  @dataclass
  class Vote:
      id: str
      voter_id: str
      target_type: str  # 'report' | 'forwarding'
      target_id: str
      value: int  # 1 | -1
      created_at: datetime
  ```
- `src/fala_gavea/domain/entities/comment.py`:
  ```python
  @dataclass
  class Comment:
      id: str
      forwarding_id: str
      author_id: str
      text: str
      created_at: datetime
  ```
- `src/fala_gavea/domain/entities/anonymous_report_token.py`:
  ```python
  @dataclass
  class AnonymousReportToken:
      id: str
      report_id: str
      token_hash: str
      created_at: datetime
  ```

**Repository ABCs** in `src/fala_gavea/domain/repositories/`:
- `vote_repository.py` — `IVoteRepository`: `cast(vote)`, `retract(voter_id, target_type, target_id)`, `get_summary(target_type, target_id, voter_id) -> VoteSummary`
- `comment_repository.py` — `ICommentRepository`: `add(comment)`, `delete(comment_id)`, `find_by_id(comment_id) -> Comment | None`, `list_by_forwarding(forwarding_id) -> list[Comment]`
- `anonymous_token_repository.py` — `IAnonymousTokenRepository`: `save(token)`, `find_report_ids_by_hash(token_hash) -> list[str]`

Add `SelfVoteError` to `src/fala_gavea/domain/exceptions.py`.

- **Files**: `src/fala_gavea/domain/entities/vote.py` (create), `src/fala_gavea/domain/entities/comment.py` (create), `src/fala_gavea/domain/entities/anonymous_report_token.py` (create), `src/fala_gavea/domain/repositories/vote_repository.py` (create), `src/fala_gavea/domain/repositories/comment_repository.py` (create), `src/fala_gavea/domain/repositories/anonymous_token_repository.py` (create), `src/fala_gavea/domain/exceptions.py` (modify)
- **Tests**: N/A (pure dataclasses and ABCs)
- [ ] Done

### Step 2: SQLAlchemy models

Add three new ORM models and update `ReportModel` in `src/fala_gavea/infrastructure/database/models.py`:

```python
# Modify ReportModel
author_id = Column(String, ForeignKey("users.id"), nullable=True)  # was nullable=False implicitly

class VoteModel(Base):
    __tablename__ = "votes"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    voter_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("voter_id", "target_type", "target_id", name="uq_vote_per_user_target"),
        CheckConstraint("value IN (1, -1)", name="ck_vote_value"),
    )

class CommentModel(Base):
    __tablename__ = "comments"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    forwarding_id = Column(String, ForeignKey("forwardings.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AnonymousReportTokenModel(Base):
    __tablename__ = "anonymous_report_tokens"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    report_id = Column(String, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    token_hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

- **Files**: `src/fala_gavea/infrastructure/database/models.py` (modify)
- **Verify**: `from fala_gavea.infrastructure.database.models import VoteModel, CommentModel, AnonymousReportTokenModel` imports cleanly
- **Tests**: N/A
- [ ] Done

### Step 3: Wipe DB and re-seed

After Wave 1 and 2 are implemented and verified:

1. Run `DELETE /admin/seed/wipe` (or delete the SQLite file directly in dev)
2. Run `uv run uvicorn fala_gavea.presentation.api.main:app` — `create_tables()` in `main.py` will call `Base.metadata.create_all()` and create all tables with the new schema
3. Re-run seed scripts in order:
   ```bash
   uv run python scripts/seed_users.py
   uv run python scripts/seed_report_types.py
   uv run python scripts/seed_relatos.py
   uv run python scripts/seed_forwardings.py
   ```

This step is manual — no code change needed. Document as a dev runbook action.

- **Files**: N/A (manual runbook step)
- **Verify**: `SELECT name FROM sqlite_master WHERE type='table'` shows `votes`, `comments`, `anonymous_report_tokens`; `PRAGMA table_info(reports)` shows `author_id` with `notnull=0`
- **Tests**: N/A
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000152 (db-schema)
