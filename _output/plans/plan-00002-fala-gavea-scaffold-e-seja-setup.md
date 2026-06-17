# DONE | 2026-06-17 17:43 UTC | Plan 000072 | CHORE-B | 2026-06-17 17:16 | fala-gavea scaffold e seja-setup | Review: light
plan_format_version: 1

source: roadmap-000071 -- Wave 0 Passo 1a e 1b: bootstrap do novo projeto fala-gavea (scaffold + harness SEJA)

## Brief (verbatim)

> roadmap 71 Wave 0 Passo 1a e 1b

## Context

Passo 1a e Passo 1b sao os dois primeiros passos manuais do Wave 0 do roadmap-000071
(gavea-seguranca-demandas-app). Eles nao geram codigo de dominio ainda -- criam a estrutura
de projeto e instalam o harness SEJA no novo diretorio `fala-gavea/`.

- **Passo 1a** (`/python-scaffold`): gera a estrutura FastAPI + SQLAlchemy + SQLite + Pydantic v2
  + pytest com a entidade `Report` como seed. Diretorio alvo: `fala-gavea/` (na raiz do workspace).
- **Passo 1b** (`/seja-setup`): instala o harness SEJA dentro de `fala-gavea/`. Configura
  `conventions.md`, `CLAUDE.md`, e as regras de acordo com a stack do projeto.

O Passo 1c (`/design`) e tratado em plan separado apos estes dois estarem concluidos.

Pre-condicao: `fala-gavea/` ainda nao existe no workspace.

---

## Steps

### Step 1: Executar /python-scaffold com entidade Report

Invocar a skill `/python-scaffold` com os seguintes argumentos:

```
/python-scaffold fala-gavea --entity Report
```

Parametros:
- **Project name / directory**: `fala-gavea`
- **Entity**: `Report`

O scaffold gera em `fala-gavea/`:
```
fala-gavea/
  pyproject.toml              # Python 3.13+, FastAPI, SQLAlchemy, Pydantic v2, pytest, uv
  README.md
  .gitignore
  .env.example
  src/fala_gavea/
    config.py
    domain/
      entities/report.py      # Dataclass Report com campos do scaffold (text, territory_level, author_id, ai_labels, likes_count)
      repositories/report_repository.py
      exceptions.py
    application/use_cases/
      create_report.py
      get_report.py
      list_reports.py
      delete_report.py
    infrastructure/
      database/session.py
      database/models.py
      repositories/sqlalchemy_report_repository.py
    presentation/
      api/main.py
      api/dependencies.py
      api/routers/reports.py
      schemas/report_schemas.py
  tests/
    conftest.py
    unit/application/test_report_use_cases.py   (~12 testes unitarios)
    integration/api/test_reports_api.py          (7 testes de integracao)
```

Nota: a entidade `Report` gerada pelo scaffold e um placeholder. Os campos reais de dominio
(lat, lon, urgency, report_type_id, photo_url, status, author_id com FK User) serao adicionados
no plan do Item 1 (Wave 0 plan seguinte). Por ora, o scaffold fornece apenas a estrutura de
camadas e os testes de sanidade.

- **Files**: `fala-gavea/` (create -- gerado pela skill)
- **References**: N/A
- **Interface**: N/A
- **Verify**: `cd fala-gavea && uv sync && uv run pytest -v` deve passar 100% (aproximadamente 19 testes gerados pelo scaffold)
- **Tests**: N/A (testes gerados automaticamente pelo scaffold; Step 2 os verifica)
- [x] Done

---

### Step 2: Verificar que o scaffold passa os testes

Apos o scaffold, verificar que a estrutura gerada esta funcionando:

```bash
cd fala-gavea
uv sync
uv run pytest -v
```

Esperar: todos os testes passam (0 failures). Se algum teste falhar, reportar antes de continuar.

Opcional (confirmar que a API sobe):
```bash
uv run uvicorn fala_gavea.presentation.api.main:app --reload
# Visitar http://localhost:8000/docs -- deve exibir Swagger UI com os endpoints CRUD de Report
```

- **Files**: N/A (verificacao apenas)
- **References**: N/A
- **Depends on**: Step 1
- **Interface**: N/A
- **Verify**: `uv run pytest` retorna exit 0; todos os testes passam
- **Tests**: N/A
- [x] Done

---

### Step 3: Executar /seja-setup para instalar o harness SEJA em fala-gavea/

Invocar a skill `/seja-setup` com o caminho do novo projeto:

```
/seja-setup fala-gavea/
```

O SEJA detectara o estado `no-harness` (fala-gavea/ existe mas nao tem .claude/) e executara
o fluxo de instalacao greenfield, que inclui:
- Copiar `.claude/skills/`, `.claude/references/`, `.claude/rules/`, `.claude/agents/`
- Gerar `product-design/conventions.md` via Section 1 questionnaire
- Scaffoldar `CLAUDE.md` com instrucoes do projeto
- Criar `product-design/constitution.md` (template base, a ser preenchido pelo /design)

**Respostas recomendadas para o Section 1 questionnaire do /seja-setup:**

| Campo | Valor |
|-------|-------|
| PROJECT_NAME | fala-gavea |
| PROJECT_DESCRIPTION | Sistema de demandas de cidadaos para seguranca urbana na Gavea: cidadao registra problema (localizacao, tipo, urgencia); agente publico cria encaminhamento para orgao; IA assiste exploracao por busca semantica e chat NL |
| PROJECT_MODE | greenfield |
| BACKEND_FRAMEWORK | FastAPI |
| BACKEND_LANGUAGE | Python 3.13 |
| DATABASE | SQLite (SQLAlchemy) |
| TESTING_STACK | pytest |
| FRONTEND_FRAMEWORK | none (HTML estatico + Leaflet -- sem framework JS) |
| DEPLOYMENT_STACK | local (uvicorn dev server + Ollama localhost:11434) |
| SRC_DIR | src/fala_gavea |
| ALL_TESTS_CMD | uv run pytest |

**Descricao de arquitetura para conventions.md (ARCHITECTURE_DESCRIPTION):**
```
FastAPI REST API com arquitetura limpa (domain/application/infrastructure/presentation).
SQLite via SQLAlchemy para persistencia. JWT Bearer (PyJWT) para autenticacao com roles
citizen/agent/admin. ChromaDB + sentence-transformers para busca semantica de relatos.
OllamaClient para chat NL como assistente de exploracao. Frontend: HTML estatico + Leaflet
servido pelo FastAPI StaticFiles.
```

**Convencoes-chave (CONVENTION_1 a CONVENTION_3):**
- CONVENTION_1: Todas as chamadas LLM e buscas semanticas passam pelo `infrastructure/` (ChromaClient, OllamaClient) -- nenhum acesso direto a ChromaDB ou Ollama em use cases ou routers
- CONVENTION_2: Autenticacao e middleware -- nenhum router acessa JWT diretamente; use `dependencies.py` (get_current_user, require_role)
- CONVENTION_3: Type annotations obrigatorias em todas as funcoes publicas; configuracao via env vars (FALA_GAVEA_OLLAMA_URL, FALA_GAVEA_OLLAMA_MODEL, DATABASE_URL)

- **Files**: `fala-gavea/.claude/` (create), `fala-gavea/product-design/conventions.md` (create), `fala-gavea/CLAUDE.md` (create), `fala-gavea/product-design/constitution.md` (create)
- **References**: N/A
- **Depends on**: Step 2
- **Interface**: N/A
- **Verify**: `fala-gavea/.claude/skills/plan/SKILL.md` existe; `fala-gavea/product-design/conventions.md` contem PROJECT_NAME=fala-gavea e SRC_DIR=src/fala_gavea
- **Tests**: N/A
- [x] Done

---

## Review: light

**Perspectives evaluated:**

| Tag | Perspective | Assessment |
|-----|------------|------------|
| ARCH | Architecture | Adopted -- scaffold usa clean architecture (domain/application/infrastructure/presentation) alinhada com D-A do roadmap-000071 |
| DX | Developer Experience | Adopted -- testes gerados pelo scaffold verificam a estrutura antes do /seja-setup |
| OPS | Operations | N/A -- sem deployment nesta etapa |

**No issues found.** Este plan e exclusivamente de bootstrap/setup -- nenhum codigo de dominio e alterado.

---

## Post-conditions

Apos este plan completo:
- `fala-gavea/` existe com estrutura FastAPI + clean architecture + testes passando
- `fala-gavea/.claude/` contem o harness SEJA instalado
- `fala-gavea/product-design/conventions.md` esta preenchido com a stack do projeto
- `fala-gavea/CLAUDE.md` esta gerado com instrucoes especificas
- O proximo passo e `/design` dentro de `fala-gavea/` (Passo 1c -- plan separado)

## Summary

All 3 steps completed successfully on 2026-06-17.

- **Step 1** (python-scaffold): `fala-gavea/` scaffolded with 39 files — FastAPI clean architecture, Report entity, 18 tests (8 integration + 10 unit).
- **Step 2** (verify tests): `uv run pytest` — 18/18 passed, 0 failures. Fixed Windows `greenlet` wheel resolution by adding `[tool.uv] required-environments` to `pyproject.toml`.
- **Step 3** (seja-setup): Harness files copied to `fala-gavea/.claude/` (skills, references, rules, agents). `product-design/conventions.md` generated with all stack values from the plan. `CLAUDE.md` scaffolded. `product-design/project/constitution.md` created with T1–T5, Q1–Q3, S1–S3 principles. `.seja-version` set to `v0.5.0`.

## Proximos passos (fora deste plan)

1. **Passo 1c** -- `/design` dentro de `fala-gavea/`: define entidades de dominio, personas, design intent alinhado ao roadmap-000071
2. **Wave 0 Item 1** -- `/plan` para adicionar as 4 entidades completas (User, Report real, ReportType, Forwarding) + auth JWT
3. **Wave 0 Item 2** -- `/plan` para ReportType CRUD (admin)
