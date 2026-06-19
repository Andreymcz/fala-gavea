# Fala Gávea

Sistema de demandas cidadãs para segurança urbana na Gávea (Rio de Janeiro).  
Cidadão registra problema (localização, tipo, urgência) → agente público cria encaminhamento para órgão responsável → IA assiste exploração por busca semântica e chat NL.

**Curso:** INF2921/CIS2114 — AI Systems Design 2026.1 | **Equipe:** Andrey, Mauro, Julia, Herbert, Natali

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.13 + FastAPI + SQLAlchemy (sync) + SQLite |
| Auth | JWT Bearer (PyJWT + bcrypt) — roles: citizen / agent / admin |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + react-leaflet |
| Semântica | ChromaDB + sentence-transformers (Wave 2) |
| LLM | Ollama local — `qwen3:8b` (Wave 2) |
| Testes | pytest (backend) + Vitest + React Testing Library (frontend) |
| Tooling | uv + ruff + pyright |

---

## Instalação

### Pré-requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Node.js 20+ e npm

### Backend

```bash
# Instalar dependências Python
uv sync --extra dev
```

### Frontend

```bash
# Instalar dependências Node
cd frontend && npm install
```

---

## Executar

### Desenvolvimento (API + SPA com hot-reload)

Abra dois terminais:

**Terminal 1 — API:**
```bash
uv run uvicorn fala_gavea.presentation.api.main:app --reload
# API disponível em http://localhost:8000
# Docs interativos: http://localhost:8000/docs
```

**Terminal 2 — Frontend (Vite dev server com proxy):**
```bash
cd frontend && npm run dev
# SPA disponível em http://localhost:5173
# Requisições /auth, /reports, /report_types, /forwardings são proxiadas para :8000
```

### Produção (SPA servida pelo FastAPI)

```bash
# 1. Build do frontend
cd frontend && npm run build   # gera static/

# 2. Subir apenas o backend (serve a SPA em /)
uv run uvicorn fala_gavea.presentation.api.main:app
# Acesse http://localhost:8000
```

### Popular tipos de problema (seed inicial)

```bash
# Cria os 8 tipos de problema padrão via API
# (com o servidor rodando)
uv run python scripts/seed_report_types.py
```

---

## Testes

```bash
# Backend
uv run pytest

# Frontend
cd frontend && npm run test

# Lint (backend)
uv run ruff check src/ tests/

# Type check (backend)
uv run pyright src/
```

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=sqlite:///./fala_gavea.db
JWT_SECRET_KEY=troque-por-uma-chave-segura-de-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# LLM local (Wave 2)
FALA_GAVEA_OLLAMA_URL=http://localhost:11434/v1
FALA_GAVEA_OLLAMA_MODEL=qwen3:8b

# ChromaDB (Wave 2)
CHROMA_PATH=./vectorstore
```

> `JWT_SECRET_KEY` é obrigatória para subir o servidor. `fala_gavea.db` é gitignored (dados locais).

---

## Arquitetura

```
src/fala_gavea/
├── domain/          # Entities (dataclasses), repository ABCs, exceptions
├── application/     # Use cases — lógica de negócio sem I/O
├── infrastructure/  # SQLAlchemy models, repos, ChromaDB, Ollama
└── presentation/
    ├── api/         # FastAPI app, routers, dependencies.py
    └── schemas/     # Pydantic request/response schemas

frontend/src/
├── auth/            # AuthContext, RequireAuth, useAuth
├── components/      # ui/ (shadcn-style), layout/
├── features/        # map/, report/, forwardings/, auth/
├── hooks/           # useReports, useReportTypes, useForwardings
└── lib/             # api.ts, types.ts, queryClient.ts
```

---

## API — Endpoints

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/auth/register` | público | Registrar cidadão |
| POST | `/auth/token` | público | Login → JWT |
| GET | `/auth/me` | bearer | Perfil do usuário |
| GET | `/reports/geojson` | público | Relatos como GeoJSON (com filtros) |
| POST | `/reports` | autenticado | Registrar relato |
| GET | `/reports/{id}` | autenticado | Detalhe do relato |
| GET | `/report_types` | público | Listar tipos ativos |
| POST | `/report_types` | admin | Criar tipo |
| PATCH | `/report_types/{id}` | admin | Atualizar tipo |
| DELETE | `/report_types/{id}` | admin | Desativar tipo (soft delete) |
| POST | `/forwardings` | agent/admin | Criar encaminhamento |
| GET | `/forwardings` | agent/admin | Listar encaminhamentos |
| GET | `/forwardings/{id}` | agent/admin | Detalhe do encaminhamento |
| PATCH | `/forwardings/{id}` | agent/admin | Atualizar encaminhamento |
| PATCH | `/forwardings/{id}/status` | agent/admin | Atualizar status |

---

## Deploy to Railway

1. Create a new Railway project and link this repo.
2. Add a **Volume** in the service settings, mounted at `/data`.
3. Set **Variables** in the Railway dashboard:
   - `DATABASE_URL=sqlite:////data/fala_gavea.db`
   - `CHROMA_DATA_DIR=/data/chromadb`
   - `JWT_SECRET=<strong random string>`
   - (Optional) `FALA_GAVEA_OLLAMA_URL` — omit to disable NL chat
4. Deploy. The `/health` endpoint is used for health checks.
