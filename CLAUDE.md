# fala-gavea

Sistema de demandas de cidadaos para seguranca urbana na Gavea: cidadao registra problema (localizacao, tipo, urgencia); agente publico cria encaminhamento para orgao; IA assiste exploracao por busca semantica e chat NL.

**Course:** INF2921/CIS2114 — AI Systems Design 2026.1 | **Team:** Andrey, Mauro, Julia, Herbert, Natali

## Stack

- **Python:** 3.13
- **Package manager:** uv
- **Framework:** FastAPI
- **Database:** SQLite + SQLAlchemy
- **Auth:** JWT Bearer (PyJWT) com roles citizen/agent/admin
- **Semantic search:** ChromaDB + sentence-transformers
- **LLM:** Ollama (local, `qwen3:8b` por padrao)
- **Frontend:** HTML estatico + Leaflet (servido pelo FastAPI StaticFiles)
- **Testing:** pytest

## Build & Run

```bash
# Install dependencies
uv sync --extra dev

# Run API server
uv run uvicorn fala_gavea.presentation.api.main:app --reload

# Run tests
uv run pytest

# Lint
uv run ruff check src/ tests/

# Type check
uv run pyright src/
```

## Architecture

FastAPI REST API com arquitetura limpa (domain/application/infrastructure/presentation). SQLite via SQLAlchemy para persistencia. JWT Bearer (PyJWT) para autenticacao com roles citizen/agent/admin. ChromaDB + sentence-transformers para busca semantica de relatos. OllamaClient para chat NL como assistente de exploracao. Frontend: HTML estatico + Leaflet servido pelo FastAPI StaticFiles.

```
src/fala_gavea/
  domain/
    entities/          # Dataclasses puros sem dependencias
    repositories/      # Interfaces (ABCs) para persistencia
    exceptions.py
  application/
    use_cases/         # Logica de negocio; sem acesso direto a DB ou HTTP
  infrastructure/
    database/          # SQLAlchemy models, session, migrations
    repositories/      # Implementacoes SQLAlchemy dos repos de dominio
    chromadb/          # ChromaClient para busca semantica
    ollama/            # OllamaClient para chat NL
  presentation/
    api/
      routers/         # FastAPI routers por entidade
      dependencies.py  # get_current_user, require_role
      main.py          # App entry point
    schemas/           # Pydantic request/response schemas
```

## Key Conventions

1. **Todas as chamadas LLM e buscas semanticas passam pelo `infrastructure/`** (ChromaClient, OllamaClient) — nenhum acesso direto a ChromaDB ou Ollama em use cases ou routers
2. **Autenticacao e middleware** — nenhum router acessa JWT diretamente; use `dependencies.py` (get_current_user, require_role)
3. **Type annotations obrigatorias** em todas as funcoes publicas; configuracao via env vars (FALA_GAVEA_OLLAMA_URL, FALA_GAVEA_OLLAMA_MODEL, DATABASE_URL)

## Skills & Design References

This project uses Claude Code skills (`.claude/skills/`). Skills are invoked via `/skill-name`. Main lifecycle: `/research` > `/plan` > `/implement` > `/check` > `/document`.

@.claude/rules/
@product-design/conventions.md

## Project Design

@product-design/project/constitution.md
@product-design/project/product-design-as-intended.md
@product-design/project/product-design-as-coded.md
@product-design/project/ux-research-results.md
@product-design/project/standards.md
@product-design/project/design-standards.md
