# /python-scaffold — Quick Guide

Generates a complete, runnable clean-architecture Python REST API project in seconds.

## What it generates

```
<project-name>/
├── pyproject.toml            # uv-managed, Python 3.13+, FastAPI + SQLAlchemy + Pydantic v2
├── README.md
├── .gitignore
├── .env.example              # DATABASE_URL=sqlite:///./app.db
├── src/
│   └── <package>/
│       ├── config.py
│       ├── domain/
│       │   ├── entities/<entity>.py       # Dataclass entity, TerritoryLevel enum, .create()
│       │   ├── repositories/<entity>_repository.py  # Abstract base
│       │   └── exceptions.py              # Typed domain exceptions
│       ├── application/
│       │   └── use_cases/
│       │       ├── create_<entity>.py
│       │       ├── get_<entity>.py
│       │       ├── list_<entity>s.py
│       │       └── delete_<entity>.py
│       ├── infrastructure/
│       │   ├── database/
│       │   │   ├── session.py             # SQLAlchemy engine + SessionLocal + Base
│       │   │   └── models.py              # ORM model
│       │   └── repositories/
│       │       └── sqlalchemy_<entity>_repository.py
│       └── presentation/
│           ├── api/
│           │   ├── main.py                # FastAPI app factory
│           │   ├── dependencies.py        # DB session injection
│           │   └── routers/<entity>s.py   # 4 CRUD endpoints
│           └── schemas/
│               └── <entity>_schemas.py    # Pydantic v2 request/response
└── tests/
    ├── conftest.py            # Fixtures: in-memory SQLite, TestClient, repo
    ├── unit/application/
    │   └── test_<entity>_use_cases.py    # ~12 unit tests (FakeRepository)
    └── integration/api/
        └── test_<entity>s_api.py         # 7 API integration tests (TestClient)
```

## Example

```
/python-scaffold fala-gavea-subsistema-a --entity CitizenPost
```

Generates `fala-gavea-subsistema-a/` with `CitizenPost` as the entity. The entity includes:
- Human input: `text`, `territory_level` (neighborhood/district/city), `territory_name`, `author_id`
- AI extension points: `ai_labels: list[str]`, `label_feedback: dict[str, bool]`
- Social signal: `likes_count: int`

## Quick start (after generation)

```bash
cd fala-gavea-subsistema-a
uv sync
uv run pytest -v          # all tests should pass
uv run uvicorn fala_gavea_subsistema_a.presentation.api.main:app --reload
```

## Portability

This skill is self-contained in `.claude/skills/python-scaffold/`. To copy it to any other SEJA repository:

```bash
cp -r .claude/skills/python-scaffold <target-repo>/.claude/skills/
```

The scaffold script uses only Python stdlib (no Jinja2, no extra deps). The **generated** project requires `uv` and Python 3.13+.
