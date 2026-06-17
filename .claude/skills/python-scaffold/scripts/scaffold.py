#!/usr/bin/env python3
"""
SEJA skill: python-scaffold
Generates a clean-architecture Python REST API project.

Usage:
    python scaffold.py --name <project-name> [--output <dir>] [--entity <EntityName>]

Example:
    python scaffold.py --name fala-gavea-subsistema-a --entity CitizenPost
"""

import argparse
import re
import sys
from pathlib import Path
from string import Template


# ── helpers ───────────────────────────────────────────────────────────────────


def camel_to_snake(name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scaffold a clean-architecture Python REST API project."
    )
    p.add_argument("--name", required=True, help="Project name in kebab-case")
    p.add_argument("--output", default=".", help="Parent directory (default: .)")
    p.add_argument(
        "--entity",
        default="Post",
        help="Main entity class name in PascalCase (default: Post)",
    )
    return p.parse_args()


def render(template: str, ctx: dict) -> str:
    return Template(template).substitute(ctx)


def write_file(base: Path, rel: str, content: str) -> None:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  created: {rel}")


# ── Step 3: project-level templates ──────────────────────────────────────────


def write_project_files(base: Path, ctx: dict) -> None:
    write_file(base, "pyproject.toml", render(PYPROJECT_TOML, ctx))
    write_file(base, "README.md", render(README_MD, ctx))
    write_file(base, ".gitignore", GITIGNORE)
    write_file(base, ".env.example", render(ENV_EXAMPLE, ctx))
    write_file(base, f"src/{ctx['package_name']}/__init__.py", "")
    write_file(base, f"src/{ctx['package_name']}/config.py", render(CONFIG_PY, ctx))


PYPROJECT_TOML = """\
[project]
name = "${project_slug}"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi[standard]>=0.115",
    "sqlalchemy>=2.0",
    "pydantic>=2.0",
    "uvicorn[standard]>=0.30",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "httpx>=0.27",
    "ruff>=0.4",
    "pyright>=1.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/${package_name}"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py313"
"""

README_MD = """\
# ${project_title}

Clean-architecture Python REST API — FastAPI + SQLAlchemy + SQLite + Pydantic v2.

## Stack

- **Python** 3.13 | **FastAPI** | **SQLAlchemy** (sync) | **Pydantic v2** | **SQLite**
- **Tests**: pytest + httpx TestClient
- **Tooling**: uv + ruff

## Quick Start

```bash
uv sync --extra dev
uv run pytest -v
uv run uvicorn ${package_name}.presentation.api.main:app --reload
```

## Architecture

```
src/${package_name}/
├── domain/           # Entities, repository interfaces, exceptions (stdlib only)
├── application/      # Use cases (domain only, no I/O)
├── infrastructure/   # SQLAlchemy models + concrete repository
└── presentation/     # FastAPI app, routers, Pydantic schemas
```

## API

| Method | Path | Status |
|--------|------|--------|
| POST   | /${entity_plural} | 201 |
| GET    | /${entity_plural} | 200 |
| GET    | /${entity_plural}/{id} | 200 / 404 |
| DELETE | /${entity_plural}/{id} | 204 / 404 |

## Environment

Copy `.env.example` to `.env` and adjust as needed.
"""

GITIGNORE = """\
__pycache__/
*.pyc
*.pyo
.venv/
.env
*.db
*.db-journal
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
"""

ENV_EXAMPLE = """\
DATABASE_URL=sqlite:///./app.db
"""

CONFIG_PY = """\
import os

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./app.db")
"""


# ── Step 4: domain layer templates ───────────────────────────────────────────


def write_domain_files(base: Path, ctx: dict) -> None:
    pkg = ctx["package_name"]
    snake = ctx["entity_snake"]
    domain = f"src/{pkg}/domain"

    write_file(base, f"{domain}/__init__.py", "")
    write_file(base, f"{domain}/exceptions.py", render(DOMAIN_EXCEPTIONS, ctx))
    write_file(base, f"{domain}/entities/__init__.py", "")
    write_file(base, f"{domain}/entities/{snake}.py", render(ENTITY_PY, ctx))
    write_file(base, f"{domain}/repositories/__init__.py", "")
    write_file(
        base,
        f"{domain}/repositories/{snake}_repository.py",
        render(REPOSITORY_INTERFACE, ctx),
    )


DOMAIN_EXCEPTIONS = """\
class DomainError(Exception):
    \"\"\"Base class for domain errors.\"\"\"


class ${entity_name}NotFoundError(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"${entity_name} not found: {id}")
        self.id = id


class InvalidInputError(DomainError):
    pass
"""

ENTITY_PY = """\
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class TerritoryLevel(str, Enum):
    NEIGHBORHOOD = "neighborhood"
    DISTRICT = "district"
    CITY = "city"


@dataclass
class ${entity_name}:
    id: str
    text: str
    territory_level: TerritoryLevel
    territory_name: str
    author_id: str
    created_at: datetime
    # AI-enrichment extension points (populated by pipeline, not by human input)
    ai_labels: list[str] = field(default_factory=list)
    label_feedback: dict[str, bool] = field(default_factory=dict)
    likes_count: int = 0

    @staticmethod
    def create(
        text: str,
        territory_level: TerritoryLevel,
        territory_name: str,
        author_id: str,
    ) -> ${entity_name}:
        return ${entity_name}(
            id=str(uuid.uuid4()),
            text=text,
            territory_level=territory_level,
            territory_name=territory_name,
            author_id=author_id,
            created_at=datetime.now(UTC),
        )
"""

REPOSITORY_INTERFACE = """\
from __future__ import annotations

from abc import ABC, abstractmethod

from ..entities.${entity_snake} import ${entity_name}


class ${entity_name}Repository(ABC):
    @abstractmethod
    def save(self, entity: ${entity_name}) -> ${entity_name}: ...

    @abstractmethod
    def find_by_id(self, id: str) -> ${entity_name} | None: ...

    @abstractmethod
    def find_all(self, limit: int = 50, offset: int = 0) -> list[${entity_name}]: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...
"""


# ── Step 5: application layer templates ──────────────────────────────────────


def write_application_files(base: Path, ctx: dict) -> None:
    pkg = ctx["package_name"]
    snake = ctx["entity_snake"]
    app_uc = f"src/{pkg}/application/use_cases"

    write_file(base, f"src/{pkg}/application/__init__.py", "")
    write_file(base, f"{app_uc}/__init__.py", "")
    write_file(base, f"{app_uc}/create_{snake}.py", render(UC_CREATE, ctx))
    write_file(base, f"{app_uc}/get_{snake}.py", render(UC_GET, ctx))
    write_file(base, f"{app_uc}/list_{snake}s.py", render(UC_LIST, ctx))
    write_file(base, f"{app_uc}/delete_{snake}.py", render(UC_DELETE, ctx))


UC_CREATE = """\
from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.${entity_snake} import ${entity_name}, TerritoryLevel
from ...domain.exceptions import InvalidInputError
from ...domain.repositories.${entity_snake}_repository import ${entity_name}Repository


@dataclass
class Create${entity_name}Input:
    text: str
    territory_level: str
    territory_name: str
    author_id: str


class Create${entity_name}:
    def __init__(self, repo: ${entity_name}Repository) -> None:
        self._repo = repo

    def execute(self, input: Create${entity_name}Input) -> ${entity_name}:
        if not input.text or len(input.text.strip()) < 5:
            raise InvalidInputError("text must be at least 5 characters")
        try:
            level = TerritoryLevel(input.territory_level)
        except ValueError:
            raise InvalidInputError(
                f"invalid territory_level: {input.territory_level!r}"
            )
        entity = ${entity_name}.create(
            text=input.text.strip(),
            territory_level=level,
            territory_name=input.territory_name,
            author_id=input.author_id,
        )
        return self._repo.save(entity)
"""

UC_GET = """\
from __future__ import annotations

from ...domain.entities.${entity_snake} import ${entity_name}
from ...domain.exceptions import ${entity_name}NotFoundError
from ...domain.repositories.${entity_snake}_repository import ${entity_name}Repository


class Get${entity_name}:
    def __init__(self, repo: ${entity_name}Repository) -> None:
        self._repo = repo

    def execute(self, id: str) -> ${entity_name}:
        entity = self._repo.find_by_id(id)
        if entity is None:
            raise ${entity_name}NotFoundError(id)
        return entity
"""

UC_LIST = """\
from __future__ import annotations

from ...domain.entities.${entity_snake} import ${entity_name}
from ...domain.repositories.${entity_snake}_repository import ${entity_name}Repository


class List${entity_name}s:
    def __init__(self, repo: ${entity_name}Repository) -> None:
        self._repo = repo

    def execute(self, limit: int = 50, offset: int = 0) -> list[${entity_name}]:
        return self._repo.find_all(limit=limit, offset=offset)
"""

UC_DELETE = """\
from __future__ import annotations

from ...domain.exceptions import ${entity_name}NotFoundError
from ...domain.repositories.${entity_snake}_repository import ${entity_name}Repository


class Delete${entity_name}:
    def __init__(self, repo: ${entity_name}Repository) -> None:
        self._repo = repo

    def execute(self, id: str) -> None:
        deleted = self._repo.delete(id)
        if not deleted:
            raise ${entity_name}NotFoundError(id)
"""


# ── Step 6: infrastructure layer templates ───────────────────────────────────


def write_infrastructure_files(base: Path, ctx: dict) -> None:
    pkg = ctx["package_name"]
    snake = ctx["entity_snake"]
    infra = f"src/{pkg}/infrastructure"

    write_file(base, f"{infra}/__init__.py", "")
    write_file(base, f"{infra}/database/__init__.py", "")
    write_file(base, f"{infra}/database/session.py", render(DB_SESSION, ctx))
    write_file(base, f"{infra}/database/models.py", render(DB_MODELS, ctx))
    write_file(base, f"{infra}/repositories/__init__.py", "")
    write_file(
        base,
        f"{infra}/repositories/sqlalchemy_{snake}_repository.py",
        render(SA_REPOSITORY, ctx),
    )


DB_SESSION = """\
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
"""

DB_MODELS = """\
from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Integer, String

from .session import Base
from ...domain.entities.${entity_snake} import TerritoryLevel


class ${entity_name}Model(Base):
    __tablename__ = "${entity_plural}"

    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    territory_level = Column(SAEnum(TerritoryLevel), nullable=False)
    territory_name = Column(String, nullable=False)
    author_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    ai_labels = Column(JSON, nullable=False, default=list)
    label_feedback = Column(JSON, nullable=False, default=dict)
    likes_count = Column(Integer, nullable=False, default=0)
"""

SA_REPOSITORY = """\
from __future__ import annotations

from sqlalchemy.orm import Session

from ...domain.entities.${entity_snake} import ${entity_name}, TerritoryLevel
from ...domain.repositories.${entity_snake}_repository import ${entity_name}Repository
from ..database.models import ${entity_name}Model


class SQLAlchemy${entity_name}Repository(${entity_name}Repository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entity: ${entity_name}) -> ${entity_name}:
        model = self._to_model(entity)
        self._session.merge(model)
        self._session.commit()
        return entity

    def find_by_id(self, id: str) -> ${entity_name} | None:
        model = self._session.get(${entity_name}Model, id)
        return self._to_entity(model) if model else None

    def find_all(self, limit: int = 50, offset: int = 0) -> list[${entity_name}]:
        models = (
            self._session.query(${entity_name}Model)
            .order_by(${entity_name}Model.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._session.get(${entity_name}Model, id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.commit()
        return True

    @staticmethod
    def _to_entity(model: ${entity_name}Model) -> ${entity_name}:
        return ${entity_name}(
            id=model.id,
            text=model.text,
            territory_level=TerritoryLevel(model.territory_level),
            territory_name=model.territory_name,
            author_id=model.author_id,
            created_at=model.created_at,
            ai_labels=model.ai_labels or [],
            label_feedback=model.label_feedback or {},
            likes_count=model.likes_count or 0,
        )

    @staticmethod
    def _to_model(entity: ${entity_name}) -> ${entity_name}Model:
        return ${entity_name}Model(
            id=entity.id,
            text=entity.text,
            territory_level=entity.territory_level,
            territory_name=entity.territory_name,
            author_id=entity.author_id,
            created_at=entity.created_at,
            ai_labels=entity.ai_labels,
            label_feedback=entity.label_feedback,
            likes_count=entity.likes_count,
        )
"""


# ── Step 7: presentation layer templates ─────────────────────────────────────


def write_presentation_files(base: Path, ctx: dict) -> None:
    pkg = ctx["package_name"]
    snake = ctx["entity_snake"]
    plural = ctx["entity_plural"]
    pres = f"src/{pkg}/presentation"

    write_file(base, f"{pres}/__init__.py", "")
    write_file(base, f"{pres}/schemas/__init__.py", "")
    write_file(base, f"{pres}/schemas/{snake}_schemas.py", render(SCHEMAS, ctx))
    write_file(base, f"{pres}/api/__init__.py", "")
    write_file(base, f"{pres}/api/dependencies.py", render(DEPENDENCIES, ctx))
    write_file(base, f"{pres}/api/routers/__init__.py", "")
    write_file(base, f"{pres}/api/routers/{plural}.py", render(ROUTER, ctx))
    write_file(base, f"{pres}/api/main.py", render(MAIN_PY, ctx))


SCHEMAS = """\
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class ${entity_name}Create(BaseModel):
    text: str
    territory_level: str
    territory_name: str
    author_id: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class ${entity_name}Response(BaseModel):
    id: str
    text: str
    territory_level: str
    territory_name: str
    author_id: str
    created_at: datetime
    ai_labels: list[str]
    label_feedback: dict[str, bool]
    likes_count: int

    model_config = {"from_attributes": True}
"""

DEPENDENCIES = """\
from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from ...infrastructure.database.session import SessionLocal
from ...infrastructure.repositories.sqlalchemy_${entity_snake}_repository import (
    SQLAlchemy${entity_name}Repository,
)


def get_${entity_snake}_repo() -> Generator[SQLAlchemy${entity_name}Repository, None, None]:
    db: Session = SessionLocal()
    try:
        yield SQLAlchemy${entity_name}Repository(db)
    finally:
        db.close()
"""

ROUTER = """\
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ${package_name}.application.use_cases.create_${entity_snake} import Create${entity_name}, Create${entity_name}Input
from ${package_name}.application.use_cases.delete_${entity_snake} import Delete${entity_name}
from ${package_name}.application.use_cases.get_${entity_snake} import Get${entity_name}
from ${package_name}.application.use_cases.list_${entity_snake}s import List${entity_name}s
from ${package_name}.domain.exceptions import ${entity_name}NotFoundError, InvalidInputError
from ${package_name}.infrastructure.repositories.sqlalchemy_${entity_snake}_repository import (
    SQLAlchemy${entity_name}Repository,
)
from ${package_name}.presentation.api.dependencies import get_${entity_snake}_repo
from ${package_name}.presentation.schemas.${entity_snake}_schemas import ${entity_name}Create, ${entity_name}Response

router = APIRouter()


@router.post("/", response_model=${entity_name}Response, status_code=status.HTTP_201_CREATED)
def create_${entity_snake}(
    body: ${entity_name}Create,
    repo: SQLAlchemy${entity_name}Repository = Depends(get_${entity_snake}_repo),
) -> ${entity_name}Response:
    try:
        entity = Create${entity_name}(repo).execute(
            Create${entity_name}Input(
                text=body.text,
                territory_level=body.territory_level,
                territory_name=body.territory_name,
                author_id=body.author_id,
            )
        )
        return ${entity_name}Response(**entity.__dict__)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=list[${entity_name}Response])
def list_${entity_plural}(
    limit: int = 50,
    offset: int = 0,
    repo: SQLAlchemy${entity_name}Repository = Depends(get_${entity_snake}_repo),
) -> list[${entity_name}Response]:
    entities = List${entity_name}s(repo).execute(limit=limit, offset=offset)
    return [${entity_name}Response(**e.__dict__) for e in entities]


@router.get("/{id}", response_model=${entity_name}Response)
def get_${entity_snake}(
    id: str,
    repo: SQLAlchemy${entity_name}Repository = Depends(get_${entity_snake}_repo),
) -> ${entity_name}Response:
    try:
        entity = Get${entity_name}(repo).execute(id)
        return ${entity_name}Response(**entity.__dict__)
    except ${entity_name}NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_${entity_snake}(
    id: str,
    repo: SQLAlchemy${entity_name}Repository = Depends(get_${entity_snake}_repo),
) -> None:
    try:
        Delete${entity_name}(repo).execute(id)
    except ${entity_name}NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
"""

MAIN_PY = """\
from __future__ import annotations

from fastapi import FastAPI

from ...infrastructure.database.session import create_tables
from .routers.${entity_plural} import router


def create_app() -> FastAPI:
    app = FastAPI(title="${project_title} API", version="0.1.0")
    create_tables()
    app.include_router(router, prefix="/${entity_plural}", tags=["${entity_plural}"])
    return app


app = create_app()
"""


# ── Step 8: test templates ────────────────────────────────────────────────────


def write_test_files(base: Path, ctx: dict) -> None:
    pkg = ctx["package_name"]
    snake = ctx["entity_snake"]
    plural = ctx["entity_plural"]

    write_file(base, "tests/__init__.py", "")
    write_file(base, "tests/conftest.py", render(TEST_CONFTEST, ctx))
    write_file(base, "tests/unit/__init__.py", "")
    write_file(base, "tests/unit/application/__init__.py", "")
    write_file(
        base,
        f"tests/unit/application/test_{snake}_use_cases.py",
        render(TEST_UNIT, ctx),
    )
    write_file(base, "tests/integration/__init__.py", "")
    write_file(base, "tests/integration/api/__init__.py", "")
    write_file(
        base,
        f"tests/integration/api/test_{plural}_api.py",
        render(TEST_INTEGRATION, ctx),
    )


TEST_CONFTEST = """\
import os

# Set DATABASE_URL before any package imports so session.py uses in-memory SQLite.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the database session module so we can monkey-patch it.
# StaticPool forces SQLAlchemy to reuse a single connection, so all sessions
# share the same in-memory SQLite database (avoids per-connection isolation).
import ${package_name}.infrastructure.database.session as _db_mod

_TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db_mod.engine = _TEST_ENGINE
_db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)

from ${package_name}.infrastructure.database.session import Base
from ${package_name}.infrastructure.repositories.sqlalchemy_${entity_snake}_repository import (
    SQLAlchemy${entity_name}Repository,
)
from ${package_name}.presentation.api.dependencies import get_${entity_snake}_repo
from ${package_name}.presentation.api.main import create_app


@pytest.fixture(autouse=True)
def reset_db() -> None:
    \"\"\"Drop and recreate all tables before each test for full isolation.\"\"\"
    Base.metadata.drop_all(_TEST_ENGINE)
    Base.metadata.create_all(_TEST_ENGINE)


@pytest.fixture
def db_session():
    session = _db_mod.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def repo(db_session):
    return SQLAlchemy${entity_name}Repository(db_session)


@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_${entity_snake}_repo] = (
        lambda: SQLAlchemy${entity_name}Repository(db_session)
    )
    return TestClient(app)
"""

TEST_UNIT = """\
import pytest

from ${package_name}.application.use_cases.create_${entity_snake} import (
    Create${entity_name},
    Create${entity_name}Input,
)
from ${package_name}.application.use_cases.delete_${entity_snake} import Delete${entity_name}
from ${package_name}.application.use_cases.get_${entity_snake} import Get${entity_name}
from ${package_name}.application.use_cases.list_${entity_snake}s import List${entity_name}s
from ${package_name}.domain.entities.${entity_snake} import ${entity_name}
from ${package_name}.domain.exceptions import (
    ${entity_name}NotFoundError,
    InvalidInputError,
)
from ${package_name}.domain.repositories.${entity_snake}_repository import ${entity_name}Repository


class FakeRepository(${entity_name}Repository):
    \"\"\"In-memory fake repository for unit testing.\"\"\"

    def __init__(self) -> None:
        self._store: dict[str, ${entity_name}] = {}

    def save(self, entity: ${entity_name}) -> ${entity_name}:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, id: str) -> ${entity_name} | None:
        return self._store.get(id)

    def find_all(self, limit: int = 50, offset: int = 0) -> list[${entity_name}]:
        items = list(self._store.values())
        return items[offset : offset + limit]

    def delete(self, id: str) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False


VALID_INPUT = Create${entity_name}Input(
    text="Precisa de mais iluminação na rua principal",
    territory_level="neighborhood",
    territory_name="Gávea",
    author_id="user-123",
)


# ── Create${entity_name} ──────────────────────────────────────────────────────


def test_create_${entity_snake}_happy_path() -> None:
    repo = FakeRepository()
    entity = Create${entity_name}(repo).execute(VALID_INPUT)
    assert entity.id is not None
    assert entity.text == VALID_INPUT.text.strip()
    assert entity.territory_level.value == "neighborhood"


def test_create_${entity_snake}_short_text_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(InvalidInputError, match="5 characters"):
        Create${entity_name}(repo).execute(
            Create${entity_name}Input(
                text="Hi",
                territory_level="city",
                territory_name="Rio",
                author_id="u1",
            )
        )


def test_create_${entity_snake}_invalid_territory_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(InvalidInputError, match="invalid territory_level"):
        Create${entity_name}(repo).execute(
            Create${entity_name}Input(
                text="Valid text here",
                territory_level="galaxy",
                territory_name="Milky Way",
                author_id="u1",
            )
        )


# ── Get${entity_name} ─────────────────────────────────────────────────────────


def test_get_${entity_snake}_found() -> None:
    repo = FakeRepository()
    created = Create${entity_name}(repo).execute(VALID_INPUT)
    found = Get${entity_name}(repo).execute(created.id)
    assert found.id == created.id


def test_get_${entity_snake}_not_found_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(${entity_name}NotFoundError):
        Get${entity_name}(repo).execute("does-not-exist")


# ── List${entity_name}s ───────────────────────────────────────────────────────


def test_list_${entity_plural}_empty() -> None:
    repo = FakeRepository()
    assert List${entity_name}s(repo).execute() == []


def test_list_${entity_plural}_multiple() -> None:
    repo = FakeRepository()
    Create${entity_name}(repo).execute(VALID_INPUT)
    Create${entity_name}(repo).execute(VALID_INPUT)
    assert len(List${entity_name}s(repo).execute()) == 2


def test_list_${entity_plural}_pagination() -> None:
    repo = FakeRepository()
    for _ in range(5):
        Create${entity_name}(repo).execute(VALID_INPUT)
    page = List${entity_name}s(repo).execute(limit=2, offset=1)
    assert len(page) == 2


# ── Delete${entity_name} ─────────────────────────────────────────────────────


def test_delete_${entity_snake}_found() -> None:
    repo = FakeRepository()
    created = Create${entity_name}(repo).execute(VALID_INPUT)
    Delete${entity_name}(repo).execute(created.id)
    assert repo.find_by_id(created.id) is None


def test_delete_${entity_snake}_not_found_raises() -> None:
    repo = FakeRepository()
    with pytest.raises(${entity_name}NotFoundError):
        Delete${entity_name}(repo).execute("ghost-id")
"""

TEST_INTEGRATION = """\
import pytest
from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "text": "Precisa de mais iluminação na rua principal",
    "territory_level": "neighborhood",
    "territory_name": "Gávea",
    "author_id": "user-abc",
}


def test_create_${entity_snake}_returns_201(client: TestClient) -> None:
    response = client.post("/${entity_plural}/", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == VALID_PAYLOAD["text"]
    assert data["territory_level"] == "neighborhood"
    assert "id" in data
    assert "created_at" in data


def test_create_${entity_snake}_empty_text_returns_422(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "text": ""}
    response = client.post("/${entity_plural}/", json=payload)
    assert response.status_code == 422


def test_create_${entity_snake}_short_text_returns_422(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "text": "Hi"}
    response = client.post("/${entity_plural}/", json=payload)
    assert response.status_code == 422


def test_get_${entity_snake}_by_id_returns_200(client: TestClient) -> None:
    created = client.post("/${entity_plural}/", json=VALID_PAYLOAD).json()
    response = client.get(f"/${entity_plural}/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_${entity_snake}_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/${entity_plural}/nonexistent-id")
    assert response.status_code == 404


def test_list_${entity_plural}_returns_200(client: TestClient) -> None:
    client.post("/${entity_plural}/", json=VALID_PAYLOAD)
    client.post("/${entity_plural}/", json=VALID_PAYLOAD)
    response = client.get("/${entity_plural}/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_${entity_snake}_returns_204(client: TestClient) -> None:
    created = client.post("/${entity_plural}/", json=VALID_PAYLOAD).json()
    response = client.delete(f"/${entity_plural}/{created['id']}")
    assert response.status_code == 204


def test_delete_${entity_snake}_not_found_returns_404(client: TestClient) -> None:
    response = client.delete("/${entity_plural}/ghost-id")
    assert response.status_code == 404
"""


# ── main scaffold function ────────────────────────────────────────────────────


def scaffold(args: argparse.Namespace) -> None:
    project_slug = args.name
    package_name = args.name.replace("-", "_")
    entity_name = args.entity
    entity_snake = camel_to_snake(entity_name)
    entity_plural = entity_snake + "s"
    project_title = project_slug.replace("-", " ").title()

    ctx = {
        "project_slug": project_slug,
        "package_name": package_name,
        "entity_name": entity_name,
        "entity_snake": entity_snake,
        "entity_plural": entity_plural,
        "project_title": project_title,
    }

    base = Path(args.output) / project_slug
    base.mkdir(parents=True, exist_ok=True)
    print(f"\nScaffolding '{project_title}' in {base.resolve()}/\n")

    write_project_files(base, ctx)
    write_domain_files(base, ctx)
    write_application_files(base, ctx)
    write_infrastructure_files(base, ctx)
    write_presentation_files(base, ctx)
    write_test_files(base, ctx)

    print(f"\nDone! {base.resolve()}")
    print("\nNext steps:")
    print(f"  cd {project_slug}")
    print("  uv sync --extra dev")
    print("  uv run pytest -v")
    print(f"  uv run uvicorn {package_name}.presentation.api.main:app --reload")


if __name__ == "__main__":
    scaffold(parse_args())
