# Roadmap 000071 | 2026-06-17 11:55 UTC | gavea-seguranca-demandas-app
spawned: plan-000072, plan-000075, plan-000079

supersedes: roadmap-000070 (scope ampliado demais; este roadmap foca no fluxo descrito)

## Brief (verbatim)

Caso de uso 1: Eu como cidadao quero fazer uma demanda para solucionar um problema de seguranca
na gavea. Cenario: Um poste da minha rua esta apagado. Abro um site, entro com a minha conta,
tiro uma foto, envio a localizacao do meu gps e escrevo uma mensagem. Quando aperto um botao,
todas estas informacoes sao enviadas para uma base de dados publica.

Caso de uso 2: Eu sou um agente publico responsavel por encaminhar demandas de cidadaos para
orgaos responsaveis. Abro um site, filtro demandas, seleciono demandas semelhantes / repetidas
e crio um encaminhamento para um orgao. O encaminhamento tem um status e solucao proposta.

Vamos nos ater primeiro ao fluxo descrito: Cidadao registra um problema (localizacao, tipo e
nivel de urgencia). Os tipos de problemas sao dinamicos e definidos pelo administrador do sistema
(criar rotas para crud). Um humano representando o poder publico tem ferramentas para explorar
os problemas e pode, a partir de um conjunto de registros, criar um encaminhamento para um orgao.
Um encaminhamento possui um status (aguardando solucao, solucao em andamento, finalizado) e contem
a solucao proposta descrita.

A IA e utilizada para ajudar o humano a explorar os dados: relatos similares, busca semantica,
chat como assistente de busca.

## Decisoes de arquitetura

**D-A: Novo projeto independente via python-scaffold**
Nao estende fala-gavea-seguranca. Novo diretorio `fala-gavea/` gerado por `/python-scaffold`.
Stack: FastAPI + SQLAlchemy + SQLite + Pydantic v2 + pytest (padrao do scaffold).

**D-B: Tipos de problema dinamicos via tabela `ReportType`**
Admin faz CRUD de tipos via API. Os tipos nao sao Enum hardcoded. Isso permite que o
administrador adicione "drenos entupidos" sem redeployar o codigo.

**D-C: Autenticacao simples para PoC**
JWT Bearer via `python-jose` ou `PyJWT`. Roles: `citizen`, `agent`, `admin`.
Sem OAuth externo -- registro via POST /auth/register + POST /auth/token.
Foto: URL string (campo opcional). Upload de imagem e future work.

**D-D: Encaminhamento como agregacao de relatos (many-to-many)**
Um `Forwarding` agrupa N relatos que o agente selecionou. Tabela `forwarding_reports` (FK dupla).
Status: `aguardando_solucao` | `solucao_em_andamento` | `finalizado`.

**D-E: IA como assistencia, nao automacao**
ChromaDB + sentence-transformers para busca semantica e relatos similares.
Chat NL como assistente de busca (reuso do padrao OllamaClient ja existente no projeto).
Sem auto-categorizacao ou sugestao automatica de encaminhamento neste roadmap.

**D-F: Frontend minimal -- HTML estatico + Leaflet**
Paginas: mapa de relatos (cidadao + agente), formulario de relato (cidadao),
painel de encaminhamentos (agente). Sem framework JS. Alpine.js para interatividade de estado.

---

## Entidades de dominio

```
User               (cidadao | agente | admin)
ReportType         (tipos dinamicos de problema -- gerenciado por admin)
Report             (demanda do cidadao: texto, localizacao, tipo, urgencia, foto)
  └── ReportType   FK
  └── User         FK (author)
Forwarding         (encaminhamento criado pelo agente para um orgao)
  └── User         FK (agent)
  └── Report[]     via ForwardingReport (many-to-many)
ForwardingReport   (join table: forwarding_id, report_id)
```

### Report
- `id: str` (UUID)
- `text: str` -- descricao do problema
- `lat: float`, `lon: float` -- localizacao GPS
- `urgency: Enum` -- `alta | media | baixa`
- `photo_url: str | None` -- URL da foto (campo livre; upload futuro)
- `report_type_id: str` FK -> ReportType
- `author_id: str` FK -> User
- `status: Enum` -- `pendente | em_analise | encaminhado | resolvido`
- `created_at: datetime`

### ReportType
- `id: str` (UUID)
- `name: str` -- ex: "Iluminacao publica", "Transito", "Vandalismo"
- `description: str | None`
- `created_at: datetime`

### Forwarding
- `id: str` (UUID)
- `institution: str` -- orgao destino (ex: "RioLuz", "COMLURB", "9a Delegacia")
- `proposed_solution: str` -- solucao proposta pelo agente
- `status: Enum` -- `aguardando_solucao | solucao_em_andamento | finalizado`
- `agent_id: str` FK -> User
- `created_at: datetime`, `updated_at: datetime`

### User
- `id: str` (UUID)
- `email: str` (unique)
- `password_hash: str`
- `name: str`
- `role: Enum` -- `citizen | agent | admin`
- `created_at: datetime`

---

## Wave Summary

### Wave 0 -- Scaffold + Dominio (sequential)

| # | ID | Title | Scope | Type | Plan | Status |
|---|-----|-------|-------|------|------|--------|
| 1 | scaffold | python-scaffold: estrutura FastAPI + dominio + auth JWT | backend | technical | plan-TBD | pending |
| 2 | report-types | ReportType CRUD (admin): POST/GET/PATCH/DELETE /report_types | backend | technical | plan-000075 | pending |

**Item 1 -- Scaffold + SEJA + dominio + auth:**

Sequencia de setup (tres passos manuais antes de qualquer /plan):

**Passo 1a -- python-scaffold:**
Executar `/python-scaffold` com entidade base `Report` para gerar a estrutura inicial em
`fala-gavea/`. O scaffold gera: FastAPI app, SQLAlchemy + SQLite, Pydantic v2, pytest,
pyproject.toml, uv.lock, e uma entidade `Report` de exemplo.

**Passo 1b -- seja-setup dentro de fala-gavea:**
Apos o scaffold, executar `/seja-setup` com o diretorio `fala-gavea/` como alvo.
Isso instala o harness SEJA (skills, references, CLAUDE.md) dentro do novo projeto.
O CLAUDE.md gerado sera customizado para esta stack e casos de uso:
- Stack: FastAPI + SQLAlchemy + SQLite + Pydantic v2 + PyJWT + ChromaDB + OllamaClient
- Casos de uso: ciudadao registra problema; agente cria encaminhamento; IA assiste exploracao
- Convencoes: arquitetura limpa (domain/application/infrastructure/presentation)

**Passo 1c -- /design dentro de fala-gavea:**
Executar `/design` dentro do contexto `fala-gavea/` para registrar formalmente:
- Entidades de dominio (User, Report, ReportType, Forwarding, ForwardingReport)
- Personas (R-P-001: Cidadao; R-P-002: Agente publico; R-P-003: Administrador)
- Design intent alinhado aos casos de uso do roadmap-000071
- Convencoes de modulo e responsabilidades

Apos os 3 passos, a estrutura alvo e:
```
fala-gavea/
  .claude/               -- harness SEJA (skills, references, rules)
  CLAUDE.md              -- instrucoes especificas do projeto
  product-design/        -- conventions.md, constitution.md, design intent
  src/fala_gavea/
    domain/entities/{user,report,report_type,forwarding}.py
    domain/repositories/*.py
    application/use_cases/*.py
    infrastructure/database/{models,session}.py
    infrastructure/repositories/sqlalchemy_*.py
    presentation/api/{main,dependencies,schemas,routers/}.py
  tests/
  pyproject.toml
```

Alem da estrutura do scaffold, o plan do Item 1 adiciona:
- Todas as 4 entidades de dominio (User, Report, ReportType, Forwarding + ForwardingReport)
- SQLAlchemy models para todas as entidades
- Auth: POST /auth/register, POST /auth/token (JWT Bearer, expiry 24h)
- Middleware: `get_current_user(token)` -> User; `require_role(role)` decorator
- `POST /reports` -- cidadao autenticado cria relato (lat, lon, urgency, text, report_type_id, photo_url?)
- `GET /reports/geojson` -- lista publica (sem auth) com filtros: type, urgency, status, since, until, bbox
- `GET /reports/{id}` -- detalhe de um relato
- Testes: register + login flow; POST /reports autenticado; GET /reports/geojson filtragem

**Item 2 -- ReportType CRUD:**

Endpoints admin (require role=admin):
- `POST /report_types` -- cria tipo
- `GET /report_types` -- lista todos (publico, sem auth -- cidadao precisa ver os tipos no form)
- `PATCH /report_types/{id}` -- edita nome/descricao
- `DELETE /report_types/{id}` -- desativa (soft delete: campo `active: bool`)

Seed script `scripts/seed_report_types.py`: 8 tipos iniciais:
`iluminacao_publica`, `transito_mobilidade`, `vandalismo`, `espaco_publico`, `lixo_conservacao`,
`seguranca_circulacao`, `conflito_social`, `outro`

Testes: CRUD completo; DELETE nao remove fisicamente; GET retorna apenas active=True.

---

### Wave 1 -- Fluxo do Agente Publico (sequential, depends on Wave 0)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 3 | forwarding | Forwarding CRUD: criar encaminhamento a partir de relatos selecionados | backend | technical | plan-000079 | scaffold | pending |
| 4 | agent-ui | Frontend: mapa de relatos + painel de encaminhamentos para agente | frontend | technical | plan-TBD | forwarding | pending |

**Item 3 -- Forwarding CRUD:**

Endpoints (require role=agent ou admin):
- `POST /forwardings` -- body: `{institution, proposed_solution, report_ids: [str]}`
  - Valida que todos os `report_ids` existem
  - Cria `Forwarding` + entradas em `forwarding_reports`
  - Atualiza `status` de cada Report para `encaminhado`
  - Retorna `ForwardingResponse` com lista de relatos linkados
- `GET /forwardings` -- lista com filtros: status, institution, agent_id, date range
- `GET /forwardings/{id}` -- detalhe com relatos linkados
- `PATCH /forwardings/{id}/status` -- body: `{status}` -- agente atualiza status
- `PATCH /forwardings/{id}` -- edita institution / proposed_solution

Schemas:
- `ForwardingCreate(institution, proposed_solution, report_ids: list[str])`
- `ForwardingStatusUpdate(status: str)`
- `ForwardingResponse(id, institution, proposed_solution, status, agent_id, reports: list[ReportSummary], created_at, updated_at)`

Use cases: `CreateForwarding`, `UpdateForwardingStatus`, `UpdateForwarding`.

Testes: criar encaminhamento com 3 relatos; verificar que relatos ficam com status=encaminhado;
PATCH /status valida enum; GET /forwardings filtra por status.

**Item 4 -- Frontend agente:**

Paginas estaticas (`fala-gavea/static/`):

`index.html` -- mapa publico (cidadao + agente):
- Leaflet + mapa centrado na Gavea
- Markers coloridos por urgencia (vermelho=alta, laranja=media, azul=baixa)
- Popup: tipo, texto, urgencia, status, data
- Sidebar: filtros categoria, urgencia, status, data_de, data_ate, bbox visivel
- Para agente autenticado: checkbox por marker para selecao multipla
- Botao flutuante "Criar encaminhamento" (aparece quando >=1 relato selecionado)
  abre modal: institution (input), proposed_solution (textarea), confirmar

`agent.html` -- painel de encaminhamentos:
- Tabela: institution, n_relatos, status, data, acoes
- Filtros: status, institution
- Click em linha expande relatos linkados
- Dropdown inline para mudar status

`login.html` -- formulario simples (email + senha -> POST /auth/token -> guarda JWT em localStorage)

`report.html` -- formulario de novo relato para cidadao autenticado:
- Select de ReportType (GET /report_types)
- Select urgencia
- Textarea texto
- Input lat/lon (botao "Usar minha localizacao" via navigator.geolocation.getCurrentPosition)
- Input photo_url (opcional)

---

### Wave 2 -- IA: Assistencia de Exploracao (parallel, depends on Wave 0)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 5 | semantic-search | ChromaDB + embeddings para busca semantica de relatos | backend | technical | plan-TBD | scaffold | pending |
| 6 | similar-reports | Endpoint /reports/{id}/similar -- relatos semanticamente proximos | backend | technical | plan-TBD | semantic-search | pending |
| 7 | chat-assistant | Chat NL como assistente de busca (OllamaClient) | backend+frontend | technical | plan-TBD | semantic-search | pending |

**Item 5 -- Semantic search:**

Reuso do padrao ChromaDB ja existente no projeto (ver `fala-gavea-seguranca/infrastructure/vector_store/chroma_client.py`):
- Nova colecao `fala-gavea-reports` em ChromaDB
- Embed `report.text` com `nomic-ai/nomic-embed-text-v1` na criacao (POST /reports)
- `GET /reports/search?q=<texto>&n=10` -- busca semantica; retorna relatos com score de similaridade
- Frontend: campo de busca na sidebar do mapa; resultado como pins roxos em layer separado

**Item 6 -- Relatos similares:**

- `GET /reports/{id}/similar?n=5` -- retorna os N relatos mais proximos semanticamente
- Util para o agente identificar duplicatas antes de criar encaminhamento
- Frontend: botao "Ver similares" no popup do marker; abre painel lateral com lista

**Item 7 -- Chat assistente:**

Reuso do padrao OllamaClient:
- `POST /chat` -- body: `{message: str, session_id: str | None}`
  - Usa ChromaDB para recuperar relatos relevantes (RAG)
  - Prompt: "Voce e um assistente que ajuda agentes publicos a explorar relatos de seguranca urbana da Gavea. Responda em pt-BR."
  - Retorna `{response: str, cited_reports: list[str]}` (IDs dos relatos usados como contexto)
- Frontend: caixa de chat flutuante no mapa; resposta exibe links para os relatos citados

---

## Execution Instructions

### Wave 0 (sequential) -- ponto de partida: novo projeto do zero
```
# Passo 1a: scaffold do projeto
/python-scaffold        # entidade: Report; diretorio: fala-gavea

# Passo 1b: instalar harness SEJA dentro do novo projeto
/seja-setup             # alvo: fala-gavea/ (companion workspace ou in-place)

# Passo 1c: definir design intent do novo projeto
/design                 # dentro de fala-gavea/ -- entidades, personas, constituicao

# Item 1: planejar e implementar o dominio completo + auth
/plan [item 1 brief]    # a partir do contexto fala-gavea/
/implement plan-TBD

# Item 2: ReportType CRUD
/plan [item 2 brief]
/implement plan-TBD
```

### Wave 1 (sequential -- depends on Wave 0)
```
/plan [item 3 brief]
/implement plan-TBD   # forwarding CRUD

/plan [item 4 brief]
/implement plan-TBD   # frontend agente
```

### Wave 2 (parallel -- depends on Wave 0 Item 1; Item 6 depends on Item 5)
```
# Sessao A:
/plan [item 5 brief] && /implement plan-TBD   # semantic search
/plan [item 6 brief] && /implement plan-TBD   # similar reports

# Sessao B (paralela a A):
# aguardar item 5 antes de iniciar item 7
/plan [item 7 brief] && /implement plan-TBD   # chat assistant
```

---

## Notes para os planos individuais

- **python-scaffold**: rodar `/python-scaffold` primeiro para gerar a estrutura base.
  Entidade sugerida para o scaffold: `Report` (entidade principal). As demais entidades
  (User, ReportType, Forwarding) serao adicionadas no plan do Item 1.

- **Auth sem biblioteca pesada**: usar `PyJWT` + `passlib[bcrypt]` para hash de senha.
  Nao usar `fastapi-users` -- adiciona complexidade desnecessaria para PoC.

- **Foto**: `photo_url` e um campo de texto (URL). O cidadao preenche manualmente ou
  futuramente via upload. Nao implementar upload de arquivo neste roadmap.

- **Geolocation no browser**: `navigator.geolocation.getCurrentPosition()` no formulario
  de relato preenche os campos lat/lon automaticamente. Fallback: campos de texto editaveis.

- **Seed de tipos**: o script de seed deve criar os 8 tipos iniciais via POST /report_types
  (nao SQL direto), para garantir que o seed exercita a API.

- **ChromaDB collection**: usar path `fala-gavea/vectorstore/` (gitignored).
  Colecao: `fala-gavea-reports`. Modelo: `nomic-ai/nomic-embed-text-v1`.

- **Ollama**: `FALA_GAVEA_OLLAMA_URL` (default `http://localhost:11434/v1`),
  `FALA_GAVEA_OLLAMA_MODEL` (default `qwen3:8b`).

- **Testes**: seguir padrao do scaffold (pytest + fixtures tmp_path para DB isolado).
  Mockar ChromaDB e Ollama em testes unitarios.
