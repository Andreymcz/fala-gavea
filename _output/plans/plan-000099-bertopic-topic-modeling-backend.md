# Plan 000099 | feat/bertopic-topics | 2026-06-19 18:33 UTC | BERTopic topic modeling backend | Review: standard
plan_format_version: 1

## User Brief

roadmap 2 wave 2. Input on BERTopic: criar espaço semantico para os reports usando o modelo. faz a
inferência de topicos a partir de um conjunto de reports, ou seja, retorna os topicos a partir de um
conjunto (permite usuario filtrar reports e ver os topicos extraidos dos mesmos)

## Agent Interpretation

**Problem**: Agentes precisam entender quais temas emergem dos relatos filtrados (por tipo, urgência,
área, data) sem precisar ler cada relato individualmente. A IA deve extrair tópicos de forma
automática sobre qualquer subconjunto que o agente esteja inspecionando.

**Approach**: Endpoint `GET /reports/topics` que recebe os mesmos filtros de `GET /reports/geojson`,
busca os relatos filtrados, roda BERTopic em modo `fit_transform` sobre esse subconjunto, e retorna
a lista de tópicos com termos representativos e contagem de documentos. A porta `ITopicModelPort` é
estendida com `infer_topics(reports) -> list[dict]` para tornar o caso de uso explícito. O modelo
BERTopic não é persistido entre chamadas (stateless on-demand), pois o subconjunto muda a cada filtro.

**Alternatives rejected**:
- *Modelo global pré-treinado + `topic_id` por relato (coluna DB)*: requer fit offline e backfill,
  mas não resolve o caso de uso central do agente — ver tópicos do *subconjunto filtrado*. Pode ser
  adicionado como wave futura.
- *BERTopic via Celery/background task*: latência de inferência (~2-10 s para 100 docs) é
  aceitável no contexto do PoC sem fila de jobs.

## Files

### New
- `src/fala_gavea/infrastructure/topics/__init__.py`
- `src/fala_gavea/infrastructure/topics/bertopic_client.py`
- `src/fala_gavea/application/use_cases/topics/__init__.py`
- `src/fala_gavea/application/use_cases/topics/get_topics_for_reports.py`
- `src/fala_gavea/presentation/schemas/topic.py`
- `tests/test_topic_modeling.py`

### Modified
- `src/fala_gavea/domain/repositories/semantic_ports.py` — adiciona `infer_topics()` à `ITopicModelPort`
- `src/fala_gavea/presentation/api/routers/reports.py` — adiciona `GET /reports/topics`
- `src/fala_gavea/presentation/api/dependencies.py` — adiciona `get_topic_model_port()`

## Best Practices

- Corpus mínimo de 3 documentos (configurável); retornar 200 com lista vazia se abaixo do threshold.
- BERTopic com `min_topic_size=2` para subconjuntos pequenos (PoC).
- Tolerância a falha: se BERTopic não convergir, logar e retornar 200 com lista vazia (não 500).
- Model instanciado na thread de request (sem estado global); sem concorrência de acesso ao modelo.
- Mock de `ITopicModelPort` em testes unitários — sem carregar modelos de embedding.
- Seguir CONVENTION_1: nenhum import de `bertopic` fora de `infrastructure/topics/`.

## Design Decisions

**User-visible impact**: O agente filtra relatos no mapa/tabela e solicita `GET /reports/topics` com
os mesmos filtros — recebe os tópicos temáticos que emergem daquele subconjunto (ex: "postes + RUA
MARQUÊS + noite" forma um tópico). O widget de Tópicos no dashboard (D-008) pode chamar este endpoint
cada vez que os filtros mudarem.

**Trade-offs accepted**: Inferência on-demand → sem estado persistido → consistente com o design
de PoC. Custo: ~2-10 s de latência por chamada no servidor (modelo BERTopic + encode). Para um PoC
com uso não-simultâneo, isso é aceitável. Se o corpus filtrado tiver <3 docs, retorna lista vazia
com grace (sem erro 4xx/5xx) para não confundir o frontend.

**Metacommunication impact**: Eu ajudo você, agente, a entender o que está acontecendo em um
conjunto específico de relatos — não no banco inteiro, mas exatamente nos que você está vendo agora.
Isso torna a exploração temática dinâmica e contextual.

## Steps

- [ ] **Step 1 — Estender ITopicModelPort com `infer_topics()`**
  - Files: `src/fala_gavea/domain/repositories/semantic_ports.py`
  - Interface: Adiciona método abstrato `infer_topics(reports: list[Report]) -> list[dict]` à
    `ITopicModelPort`. Cada dict: `{"topic_id": int, "terms": list[str], "count": int}`.
  - Tests: N/A (interface pura; sem comportamento próprio)
  - Verify: `pyright src/` sem erros adicionais

- [ ] **Step 2 — `infrastructure/topics/bertopic_client.py`**
  - Files: `src/fala_gavea/infrastructure/topics/__init__.py`,
    `src/fala_gavea/infrastructure/topics/bertopic_client.py`
  - References: `src/fala_gavea/infrastructure/embeddings/registry.py` (SemanticConfig)
  - Interface: `class BERTopicClient(ITopicModelPort):`
    - `__init__(self, config: SemanticConfig)` — carrega SentenceTransformer para `topics` purpose
    - `infer_topics(reports)` — cria BERTopic(embedding_model=…, min_topic_size=2), roda
      `fit_transform(texts)`, retorna lista de dicts `{topic_id, terms, count}` excluindo tópico `-1`
      (outliers); em caso de exceção, loga e retorna `[]`
    - `fit(reports)`, `topic_of(report)`, `list_topics()` — implementações stub (NotImplementedError
      com mensagem explicativa); reservadas para futura batch mode
  - Tests: N/A para esta step (testado em Step 8)
  - Verify: arquivo criado; `ruff check` sem erros

- [ ] **Step 3 — Use case `GetTopicsForReports`**
  - Files: `src/fala_gavea/application/use_cases/topics/__init__.py`,
    `src/fala_gavea/application/use_cases/topics/get_topics_for_reports.py`
  - Interface: `class GetTopicsForReports:` com `execute(reports: list[Report]) -> list[dict]`.
    Recebe lista de `Report` (já filtrada pelo caller), valida corpus mínimo (3 docs), chama
    `self._topic_port.infer_topics(reports)`, retorna resultado.
  - Tests: N/A para esta step (testado em Step 8)
  - Verify: importável sem erros

- [ ] **Step 4 — Schema de resposta `TopicItem` + `TopicListResponse`**
  - Files: `src/fala_gavea/presentation/schemas/topic.py`
  - Interface:
    ```python
    class TopicItem(BaseModel):
        topic_id: int
        terms: list[str]
        count: int

    class TopicListResponse(BaseModel):
        topics: list[TopicItem]
        total_reports: int  # total docs passados para o modelo
    ```
  - Tests: N/A
  - Verify: `pyright` sem erros no arquivo

- [ ] **Step 5 — Dependency provider `get_topic_model_port()`**
  - Files: `src/fala_gavea/presentation/api/dependencies.py`
  - Interface: Função `get_topic_model_port() -> ITopicModelPort | None` — instancia
    `BERTopicClient(SemanticConfig())` com lazy init + singleton (mesmo padrão de `get_report_indexer`);
    loga e retorna `None` se falhar (bertopic/sentence-transformers não instalados).
  - Tests: N/A
  - Verify: `get_topic_model_port()` importável; singleton lazy funciona

- [ ] **Step 6 — Endpoint `GET /reports/topics`**
  - Files: `src/fala_gavea/presentation/api/routers/reports.py`
  - Interface: Novo endpoint **antes** de `GET /{id}` na ordem de registro:
    ```
    GET /reports/topics?type_id=&urgency=&status=&since=&until=&bbox=&min_docs=3
    ```
    Reutiliza `ReportFiltersQuery`. Requer autenticação (`get_current_user`). Retorna
    `TopicListResponse`. Se `topic_port is None`, 503. Se `len(reports) < min_docs`, retorna
    `TopicListResponse(topics=[], total_reports=len(reports))`. Chama `GetTopicsForReports(topic_port).execute(reports)`.
  - Tests: N/A para esta step (testado em Step 7)
  - Verify: `uv run uvicorn … &` + `curl /reports/topics` retorna 200 (com auth)

- [ ] **Step 7 — Testes unitários**
  - Files: `tests/test_topic_modeling.py`
  - Tests:
    - "quando infer_topics recebe lista vazia, retorna lista vazia" — mock ITopicModelPort
    - "quando corpus < min_docs (ex: 2 reports), GetTopicsForReports retorna lista vazia sem chamar port"
    - "quando corpus >= min_docs, GetTopicsForReports chama infer_topics e retorna resultado do port"
    - "GET /reports/topics com topic_port=None retorna 503"
    - "GET /reports/topics com 0 relatos filtrados retorna 200 com topics=[]"
    - "GET /reports/topics sem auth retorna 401"
  - Verify: `uv run pytest tests/test_topic_modeling.py -v` — todos os testes passam

## Outcomes

- `GET /reports/topics` disponível; aceita os mesmos filtros de `GET /reports/geojson`
- BERTopic executa on-demand sobre o subconjunto filtrado
- `ITopicModelPort.infer_topics()` é a abstração canônica para extração de tópicos
- Corpus mínimo e tolerância a falha garantidos
- Testes unitários cobrem os casos de borda sem carregar modelos reais
- `smoke: true`

---

## Review Log

### Phase 1 — Perspective Triage

Shortlist para feat/backend-IA: **ARCH**, **PERF**, **TEST**, **API**

| Perspective | Status | Concern |
|-------------|--------|---------|
| ARCH | Adopted | BERTopicClient fica em `infrastructure/topics/`; nenhum import de bertopic fora dessa camada. Use case em `application/`. CONVENTION_1 respeitada. |
| PERF | Deferred | BERTopic fit_transform pode levar 2-30 s dependendo do corpus e do modelo; sem cache entre chamadas com os mesmos filtros. |
| TEST | Adopted | 6 testes unitários cobrem os casos de borda sem dependência de rede ou modelo real. |
| API | Adopted | Endpoint segue padrão existente (`GET /reports/…`); reutiliza `ReportFiltersQuery`; retorna 503 graciosamente quando port indisponível. |
| SEC | N/A | Endpoint protegido por `get_current_user`. Nenhuma credencial nova. |
| DB | N/A | Nenhuma migração; não persiste topic_id. |

**PERF — Phase 2 trigger?** A latência de inferência é real, mas em PoC com uso não-simultâneo é
aceitável. O deferred concern é registrado como nota (não blocking). Não é Phase 2: nenhuma
regressão, nenhuma violação de standard — é uma limitação documentada.

### Execution Metrics

| Metric | Value |
|--------|-------|
| Perspectives loaded | 4 |
| Phase 2 triggered | No |
| Iterations | 1 |
| Plan amendments | 0 |
| Final status | Adopted / Deferred-with-rationale |

**PERF note (documented deferral)**: BERTopic fit_transform é O(n·d) em CPU; para subconjuntos de
até ~500 relatos o tempo estimado é <10 s no hardware típico de PoC. Caching por filtro hash e
BackgroundTasks são evolution paths documentados mas fora de escopo do plano atual.
