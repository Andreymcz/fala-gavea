---
designer_description: "Engineering standards for fala-gavea — backend layering (clean architecture), testing style, and stack conventions so every PR can be reviewed against one agreed baseline."
---

# ENGINEERING STANDARDS — fala-gavea

---

## Backend

### 1. Project Structure

Clean architecture com quatro camadas. Nenhuma camada pode importar de uma camada superior (domain ← application ← infrastructure ← presentation).

```
src/fala_gavea/
├── domain/
│   ├── entities/          # Dataclasses puros sem dependencias externas
│   │   ├── user.py
│   │   ├── report.py
│   │   ├── report_type.py
│   │   └── forwarding.py
│   ├── repositories/      # Interfaces (ABCs) — sem import de SQLAlchemy
│   │   ├── user_repo.py
│   │   ├── report_repo.py
│   │   └── forwarding_repo.py
│   └── exceptions.py      # Excecoes de dominio
├── application/
│   └── use_cases/         # Logica de negocio; sem acesso direto a DB ou HTTP
│       ├── auth/
│       ├── reports/
│       └── forwardings/
├── infrastructure/
│   ├── database/
│   │   ├── models.py      # SQLAlchemy ORM models
│   │   └── session.py     # SessionLocal, engine, get_db
│   ├── repositories/      # Implementacoes SQLAlchemy dos repos de dominio
│   │   ├── sqlalchemy_user_repo.py
│   │   ├── sqlalchemy_report_repo.py
│   │   └── sqlalchemy_forwarding_repo.py
│   ├── chromadb/
│   │   └── chroma_client.py   # ChromaClient para busca semantica
│   └── ollama/
│       └── ollama_client.py   # OllamaClient para chat NL
└── presentation/
    ├── api/
    │   ├── main.py            # App entry point; inclui routers
    │   ├── dependencies.py    # get_current_user, require_role
    │   └── routers/           # FastAPI routers por entidade
    │       ├── auth.py
    │       ├── reports.py
    │       ├── report_types.py
    │       └── forwardings.py
    └── schemas/               # Pydantic request/response schemas
        ├── auth.py
        ├── report.py
        ├── report_type.py
        └── forwarding.py
```

### 2. Layer Boundaries

| Layer | May import | Must NOT import |
|-------|-----------|-----------------|
| domain | stdlib, dataclasses | SQLAlchemy, FastAPI, Pydantic, requests |
| application | domain | SQLAlchemy, FastAPI, HTTP clients |
| infrastructure | domain, application, SQLAlchemy, ChromaDB, httpx | FastAPI, presentation |
| presentation | domain, application, infrastructure, FastAPI, Pydantic | — |

### 3. Entity Conventions

- Entities em `domain/entities/` são `@dataclass` puros (ou Pydantic BaseModel sem validacao de DB).
- Nenhum import de SQLAlchemy em entities.
- IDs são UUIDs gerados na camada de aplicacao ou na repository (nao pelo DB).

### 4. Repository Pattern

- Interfaces em `domain/repositories/` são ABCs com typings completos.
- Implementacoes em `infrastructure/repositories/` herdam da interface.
- Use cases recebem a interface via injecao de dependencia (FastAPI Depends).
- Nenhum use case importa SQLAlchemy diretamente.

### 5. Authentication & Authorization

- JWT Bearer via PyJWT. Token expiry: 24h. Algorithm: HS256.
- `dependencies.py` expoe:
  - `get_current_user(token: str) -> User` — decodifica JWT, levanta 401 se invalido.
  - `require_role(role: str) -> Depends` — levanta 403 se role nao confere.
- Nenhum router acessa JWT diretamente — sempre via `Depends(get_current_user)`.
- Password hashing: passlib[bcrypt] com `CryptContext(schemes=["bcrypt"])`.

### 6. Infrastructure Clients

- `ChromaClient` em `infrastructure/chromadb/`: encapsula colecao `fala-gavea-reports`, expoe `add_report(id, text)`, `search(query, n) -> list[str]`, `get_similar(report_id, n) -> list[str]`.
- `OllamaClient` em `infrastructure/ollama/`: encapsula POST /chat/completions, expoe `chat(message, context_reports) -> str`.
- Nenhum router ou use case importa chromadb ou httpx diretamente.
- URLs/modelos via env vars: `FALA_GAVEA_OLLAMA_URL`, `FALA_GAVEA_OLLAMA_MODEL`, `CHROMA_PATH`.

### 7. Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./fala_gavea.db` | SQLAlchemy URL |
| `JWT_SECRET_KEY` | — (required) | Secret para assinar JWTs |
| `JWT_ALGORITHM` | `HS256` | — |
| `JWT_EXPIRY_HOURS` | `24` | — |
| `FALA_GAVEA_OLLAMA_URL` | `http://localhost:11434/v1` | URL do servidor Ollama |
| `FALA_GAVEA_OLLAMA_MODEL` | `qwen3:8b` | Modelo Ollama para chat |
| `CHROMA_PATH` | `./vectorstore` | Path do ChromaDB |

### 8. API Conventions

- Todos os endpoints retornam JSON.
- Erros retornam `{"detail": "mensagem"}` no formato FastAPI padrao.
- IDs nos paths sao UUIDs (str).
- Paginacao: `?skip=0&limit=50` nos endpoints de listagem.
- GeoJSON: GET /reports/geojson retorna FeatureCollection padrao GeoJSON.

### 9. Database

- SQLite via SQLAlchemy (modo sincrono para simplicidade no PoC).
- `fala_gavea.db` gitignored (constituicao T4).
- Criacao de tabelas via `Base.metadata.create_all(engine)` no startup (sem Alembic no PoC).
- Session management: `Depends(get_db)` nos routers.

---

## Frontend

### 1. Structure

```
static/
├── index.html    # Mapa publico + interface do agente
├── report.html   # Formulario de novo relato (cidadao autenticado)
├── agent.html    # Painel de encaminhamentos (agente)
└── login.html    # Formulario de login
```

### 2. Stack

- HTML5 semantico. Sem framework de build (sem npm, webpack, etc.).
- Leaflet 1.9+ para mapas (CDN).
- Alpine.js 3+ para reatividade (CDN) — checkboxes, modais, filtros, estado de login.
- CSS inline ou `<style>` embarcado — sem Tailwind, sem CSS frameworks no PoC.

### 3. Auth State

- JWT armazenado em `localStorage['fala_gavea_token']`.
- Cada pagina verifica token ao carregar; se ausente/expirado, redireciona para login.html.
- Requests autenticados: `Authorization: Bearer <token>` header.

### 4. Map Conventions

- Centro padrao: Gavea (-22.9731, -43.2272), zoom 15.
- Marcadores coloridos por urgencia: vermelho (alta), laranja (media), azul (baixa).
- Layer separado (roxo) para resultados de busca semantica.
- Clustering de marcadores proximos via leaflet.markercluster.

---

## Testing

### 1. Framework

- pytest + pytest-asyncio (se necessario para testes async).
- Banco de dados de teste: SQLite in-memory (`sqlite:///:memory:`) via fixture `tmp_path`.
- ChromaDB e OllamaClient: mockados em testes unitarios.

### 2. Test Organization

```
tests/
├── conftest.py          # Fixtures: test_client, db_session, auth_headers
├── test_auth.py         # register + login flow; token validation
├── test_reports.py      # POST /reports; GET /reports/geojson com filtros
├── test_report_types.py # CRUD admin
├── test_forwardings.py  # Criar encaminhamento; status transition; GET com filtros
└── test_search.py       # Busca semantica (mocked ChromaDB)
```

### 3. Coverage Expectations

- Minimo: auth flow, POST /reports, GET /reports/geojson, POST /forwardings.
- `uv run pytest` deve passar antes de qualquer commit.
- Mockar sempre ChromaDB e OllamaClient — testes nao requerem servicos externos.

### 4. Fixture Pattern

```python
# conftest.py
@pytest.fixture
def db_session(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def test_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

---

## Security

### 1. Input Validation

- Todos os inputs validados via Pydantic schemas antes de chegar aos use cases.
- Limites em `product-design-as-intended.md §10`.
- Coordenadas GPS validadas: lat em [-90, 90], lon em [-180, 180].

### 2. Auth Boundaries

- Endpoints publicos (sem auth): GET /reports/geojson, GET /report_types, POST /auth/register, POST /auth/token.
- Todos os demais requerem `Depends(get_current_user)`.
- Endpoints de escrita de admin requerem `Depends(require_role("admin"))`.

### 3. Secrets

- `JWT_SECRET_KEY` obrigatoriamente via env var — nunca hardcoded.
- `fala_gavea.db` gitignored.
- Sem API keys de LLM externo (Ollama e local — conforme C1 da constituicao).

### 4. SQL Injection

- Nunca interpolar strings em queries SQLAlchemy — usar parametros bindados.
- ORM cobre a maioria dos casos; raw SQL requer `text()` com parametros.
