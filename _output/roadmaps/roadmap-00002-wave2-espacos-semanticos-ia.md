# Roadmap 000088 | 2026-06-18 20:04 UTC | wave2 espacos semanticos IA
spawned: plan-000089, plan-000090, plan-000090

refina: roadmap-000071 Wave 2 (itens 5 semantic-search, 6 similar-reports, 7 chat-assistant)

A Wave 2 original assumia uma unica colecao ChromaDB com um unico modelo. Este roadmap
substitui essa premissa pela arquitetura de **multiplos espacos semanticos especializados por
proposito** (decisao do usuario) e adiciona um pipeline de ingestao que indexa cada relato nos
espacos no momento da criacao, alem de clusterizacao por topicos (BERTopic) e RAG.

## Source
- _output/roadmaps/roadmap-00001-gavea-seguranca-demandas-app.md (read -- Wave 2 original)
- _output/reflections/reflection-000086-estado-atual-crud-vs-roadmap.md (read -- estado atual)
- product-design/project/product-design-as-intended.md (read -- intencao IA-como-assistencia)
- product-design/project/conventions.md (read -- paths, convencoes)
- src/fala_gavea/application/use_cases/reports/create_report.py (read -- ponto de hook de ingestao)
- src/fala_gavea/presentation/api/dependencies.py (read -- padrao de DI)
- pyproject.toml (read -- deps de IA ainda nao instaladas)

## Brief (verbatim)

roadmap 1 wave 2. O foco desta etapa eh preparar o sistema para realizar operacoes em um espaço
semantico: busca de relatos similares, RAG, clusterização etc. Pensando agora, acho que pode ser
interessante usarmos modelos diferentes a depender da aplicacao: BERTopic para extrair topicos,
outros modelos para criar espaco semantico para busca por similaridade, RAG etc.
Ao receber a criacao de um relato, precisamos adicionar aos espacos semanticos da aplicacao para
dar suporte as features de IA

---

## Estado de partida (relevante)

- Wave 0 e Wave 1 do roadmap-000071 estao **implementadas** (14 endpoints, SPA React, auth JWT).
- Nenhuma infra semantica existe ainda: `infrastructure/chromadb/` e `infrastructure/ollama/`
  **nao existem**; `chromadb`, `sentence-transformers`, `bertopic`, cliente Ollama **nao estao**
  no `pyproject.toml` (apesar de citados no CLAUDE.md).
- Ja existem **~10k relatos** no banco (seed de 1 ano, plan-000085) criados **antes** de qualquer
  espaco semantico -> backfill obrigatorio.
- `CreateReport.execute()` recebe `report_repo` + `report_type_repo` e retorna `Report`; o hook de
  ingestao entra aqui via porta de dominio.

---

## Decisoes de arquitetura

**D-A: Registry de provedores de embedding por proposito (multiplos modelos especializados)**
Em vez de um modelo unico, um registry mapeia *proposito -> modelo*:
- `search` / `rag` -> modelo de recuperacao multilingue (default sugerido: `intfloat/multilingual-e5-base`)
- `topics` -> backbone do BERTopic (default sugerido: `paraphrase-multilingual-MiniLM-L12-v2`)

Configuravel por env vars (`FALA_GAVEA_EMBED_MODEL_SEARCH`, `FALA_GAVEA_EMBED_MODEL_TOPICS`).
No PoC `search` e `rag` podem apontar para o mesmo modelo; a abstracao permite divergir depois sem
mexer em use cases. Acesso sempre via porta de dominio (CONVENTION_1).

**D-B: Espacos semanticos = colecoes/artefatos distintos por proposito**
Colecao ChromaDB `falagavea_reports_search` para recuperacao (busca semantica, similares, contexto
de RAG); artefato BERTopic persistido separadamente (`vectorstore/topics/`). Path `vectorstore/`
gitignored. Indexacao de cada espaco e independente.

**D-C: Indexacao na criacao via porta de dominio**
`CreateReport` recebe uma porta `IReportIndexer` (dominio) e chama `index(report)` **apos**
`report_repo.save()`. Implementacao ChromaDB vive em `infrastructure/`. Indexacao **sincrona** no
PoC (latencia do encode aceitavel); nota de evolucao: migravel para `BackgroundTasks`/fila se a
latencia do POST /reports incomodar. Falha de indexacao nao deve derrubar a criacao do relato
(log + relato fica pendente de reindex).

**D-D: Backfill dos relatos existentes**
Script `scripts/backfill_semantic.py` indexa todos os relatos ja persistidos nas colecoes de busca
e (re)treina o BERTopic sobre o corpus. Idempotente (pula ids ja indexados). Necessario pelos ~10k
seeds anteriores a esta infra.

**D-E: BERTopic em lote + atribuicao incremental**
O modelo BERTopic e treinado em lote sobre o corpus (`fit`) e persistido. Relatos novos recebem
`topic_id` via `transform()` na criacao (ou em batch). Armazenamento da atribuicao: avaliar coluna
`topic_id` nullable em `Report` (migracao) vs. tabela `report_topics`. Topicos expostos via
`GET /reports/topics` (lista + contagem + termos representativos por topico).

**D-F: RAG reutiliza o espaco de busca, com provedor de LLM plugavel (Ollama OU Anthropic)**
`POST /chat` recupera top-k relatos do espaco `search`, monta contexto pt-BR de assistente de
exploracao e chama o LLM via porta de dominio `ILLMClient`. Duas implementacoes, selecionadas por
env var `FALA_GAVEA_LLM_PROVIDER` (`ollama` | `anthropic`):
- `ollama` (default): `OllamaClient` local — `FALA_GAVEA_OLLAMA_URL` (`http://localhost:11434/v1`),
  `FALA_GAVEA_OLLAMA_MODEL` (`qwen3:8b`). Dados ficam locais.
- `anthropic`: `AnthropicClient` via SDK oficial `anthropic`; `ANTHROPIC_API_KEY` resolvido do
  ambiente (nao hardcoded); modelo default `claude-haiku-4-5` (o mais barato, $1/$5 por 1M tokens —
  adequado a um assistente de busca de PoC), override por `FALA_GAVEA_ANTHROPIC_MODEL`.
  Mesma abstracao do registry de embeddings (D-A): provider por config, sem acoplar use cases.
Retorna `{response, cited_report_ids}`. Sem auto-categorizacao nem auto-encaminhamento
(IA-como-assistencia, conforme product-design-as-intended.md).

> **Atencao a privacidade (escolha de provider):** o design-intent define "privacidade de dados
> cidadaos (local-only)". `ollama` mantem o texto dos relatos local; `anthropic` envia o contexto
> recuperado (textos de relatos) para a API externa. Escolher o provider conforme a necessidade de
> privacidade do deployment; default `ollama` preserva o local-only.

**D-G: Frontend de IA na SPA React existente**
As features entram na SPA React (plan-000082), nao em paginas estaticas: busca semantica como layer
no mapa, painel "Ver similares", filtro/visualizacao de topicos, caixa de chat com links para os
relatos citados.

---

## Portas e componentes novos

```
domain/repositories/ (ports)
  IReportIndexer          index(report) / delete(report_id) / reindex_all()
  ISemanticSearchPort     search(query, n) -> [(report_id, score)]
                          similar(report_id, n) -> [(report_id, score)]
  ITopicModelPort         topic_of(report) / list_topics() / fit(corpus)
  ILLMClient              complete(system, messages) -> str  (Ollama | Anthropic)

infrastructure/
  embeddings/registry.py          EmbeddingProviderRegistry (proposito -> modelo)
  chromadb/chroma_search_client.py  implementa IReportIndexer + ISemanticSearchPort
  topics/bertopic_model.py        implementa ITopicModelPort (fit/transform/persist)
  llm/ollama_client.py            ILLMClient local (Ollama)
  llm/anthropic_client.py         ILLMClient via SDK anthropic (default claude-haiku-4-5)
  llm/factory.py                  resolve ILLMClient por FALA_GAVEA_LLM_PROVIDER

application/use_cases/
  reports/search_reports.py       busca semantica
  reports/find_similar_reports.py similares
  topics/list_topics.py           lista topicos + contagens
  chat/answer_with_rag.py         RAG: recupera contexto + chama Ollama
```

---

## Wave Summary

### Wave 0 -- Fundacao semantica (sequential)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 1 | semantic-infra | Deps de IA + EmbeddingProviderRegistry + ChromaClient + portas de dominio + config env | backend | technical | plan-000089 | -- | done |
| 2 | ingestion-pipeline | Hook de indexacao em CreateReport (porta IReportIndexer) + backfill dos ~10k relatos | backend | technical | plan-000090 | semantic-infra | pending |

**Item 1 -- semantic-infra:**
Adiciona ao `pyproject.toml`: `chromadb`, `sentence-transformers`, `bertopic`, e cliente Ollama
(httpx ja vem com fastapi[standard]). Cria: `EmbeddingProviderRegistry` (D-A); `ChromaSearchClient`
em `infrastructure/chromadb/`; portas de dominio `IReportIndexer`, `ISemanticSearchPort`,
`ITopicModelPort`; config via env vars (`FALA_GAVEA_EMBED_MODEL_SEARCH`, `_TOPICS`,
`FALA_GAVEA_VECTORSTORE_PATH`). Colecao `falagavea_reports_search`. Testes: registry resolve modelo
por proposito; ChromaClient indexa+consulta (mock do modelo de embedding em unit; smoke real opcional).

**Item 2 -- ingestion-pipeline:**
Injeta `IReportIndexer` em `CreateReport` (atualiza `dependencies.py` + router). Indexa o relato na
colecao de busca apos `save()` (D-C, sincrono, tolerante a falha). Script `scripts/backfill_semantic.py`
idempotente para os relatos existentes (D-D). Testes: criar relato chama o indexer; falha de index
nao impede a criacao; backfill pula ids ja indexados.

---

### Wave 1 -- Features de busca (parallel, depends on Wave 0)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 3 | semantic-search | GET /reports/search?q=&n= -- busca semantica com score | backend | technical | plan-TBD | ingestion-pipeline | pending |
| 4 | similar-reports | GET /reports/{id}/similar?n= -- vizinhos semanticos de um relato | backend | technical | plan-TBD | ingestion-pipeline | pending |

**Item 3 -- semantic-search:**
Use case `SearchReports` + endpoint `GET /reports/search?q=<texto>&n=10`; consulta `ISemanticSearchPort`,
hidrata `Report` por id, retorna lista com `score`. Publico (alinhado a `GET /reports/geojson`).

**Item 4 -- similar-reports:**
Use case `FindSimilarReports` + endpoint `GET /reports/{id}/similar?n=5`. Util para o agente detectar
duplicatas antes de encaminhar. 404 se o relato base nao existe; exclui o proprio relato do resultado.

---

### Wave 2 -- Topicos & RAG (parallel, depends on Wave 0; rag-chat usa o espaco de busca)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 5 | topic-modeling | BERTopic: fit em lote + atribuicao incremental + GET /reports/topics | backend | technical | plan-TBD | semantic-infra | pending |
| 6 | rag-chat | POST /chat -- RAG via Ollama recuperando relatos do espaco de busca | backend | technical | plan-TBD | semantic-search | pending |

**Item 5 -- topic-modeling:**
`infrastructure/topics/bertopic_model.py` (D-E): `fit(corpus)` em lote + persistencia em
`vectorstore/topics/`; `transform(report)` para atribuicao incremental na criacao. Armazenamento da
atribuicao (coluna `topic_id` vs tabela -- decidir no plano). `GET /reports/topics` lista topicos com
contagem e termos representativos. Inclui job/comando de (re)treino (`scripts/fit_topics.py` ou
subcomando). Testes: fit sobre corpus pequeno; transform atribui topico; endpoint agrega contagens.

**Item 6 -- rag-chat:**
Provedor de LLM plugavel em `infrastructure/llm/` (porta `ILLMClient`): `OllamaClient` (default) e
`AnthropicClient` (SDK oficial `anthropic`, dep nova; default `claude-haiku-4-5`), resolvidos por
`llm/factory.py` via `FALA_GAVEA_LLM_PROVIDER` (D-F). Use case `AnswerWithRag` + `POST /chat`
(`{message, session_id?}` -> `{response, cited_report_ids}`). Recupera top-k via `ISemanticSearchPort`,
monta prompt pt-BR de assistente, chama `ILLMClient`. Mock do `ILLMClient` em testes unitarios
(sem rede para nenhum provider). Require role `agent`/`admin` (alinhado a §8 permissions: chat NL e do
agente).

---

### Wave 3 -- Frontend de IA na SPA (parallel, depends on backends respectivos)

| # | ID | Title | Scope | Type | Plan | Depends on | Status |
|---|-----|-------|-------|------|------|-----------|--------|
| 7 | ai-search-frontend | SPA: busca semantica (layer no mapa) + painel "Ver similares" | frontend | design | plan-TBD | semantic-search, similar-reports | pending |
| 8 | ai-chat-topics-frontend | SPA: caixa de chat RAG (links p/ relatos citados) + filtro/visualizacao de topicos | frontend | design | plan-TBD | rag-chat, topic-modeling | pending |

**Item 7 -- ai-search-frontend:**
Campo de busca na sidebar do mapa; resultados como layer distinto (pins) com score. Botao
"Ver similares" no popup do marker -> painel lateral com a lista de similares (clicaveis no mapa).

**Item 8 -- ai-chat-topics-frontend:**
Caixa de chat flutuante no mapa; a resposta renderiza links para os `cited_report_ids`. Filtro por
topico na sidebar (a partir de `GET /reports/topics`); opcional: visao agregada de topicos.

---

## Execution Instructions

### Wave 0 (sequential) -- caminho critico
```
/plan [item 1: semantic-infra]      && /implement plan-TBD
/plan [item 2: ingestion-pipeline]  && /implement plan-TBD
```
Pre-requisito de ambiente: ChromaDB instala local (pip); modelos sentence-transformers baixam no
primeiro uso (cache HF). Ollama precisa estar rodando em `localhost:11434` com `qwen3:8b` para o
item 6 -- verificar antes de iniciar a Wave 2.

### Wave 1 (parallel -- depends on Wave 0)
```
# Sessao A:
/plan [item 3: semantic-search]  && /implement plan-TBD
# Sessao B (paralela):
/plan [item 4: similar-reports]  && /implement plan-TBD
```

### Wave 2 (parallel -- depends on Wave 0; item 6 depends on item 3)
```
# Sessao A:
/plan [item 5: topic-modeling]   && /implement plan-TBD
# Sessao B (apos item 3):
/plan [item 6: rag-chat]         && /implement plan-TBD
```

### Wave 3 (parallel -- depends on backends; itens de design via metacomm framing)
```
/plan --framing metacomm [item 7: ai-search-frontend]      && /implement plan-TBD
/plan --framing metacomm [item 8: ai-chat-topics-frontend] && /implement plan-TBD
```

Execucao paralela: multiplas sessoes Claude Code, ou agentes worktree-isolados a partir de uma
sessao. O `Plan` column comeca como `plan-TBD`; preencher com o ID real **apos** `/plan` reservar.

---

## Notes para os planos individuais

- **Latencia de embedding na criacao**: encode sincrono no POST /reports. Se incomodar, mover para
  `BackgroundTasks`. Decidir no plano do item 2; manter a porta agnostica a sincronia.
- **Tolerancia a falha de indexacao**: criacao do relato nao pode falhar por erro de ChromaDB.
  Logar e seguir; o backfill/reindex cobre relatos pendentes.
- **Atribuicao de topico**: decidir coluna `topic_id` (migracao SQLAlchemy) vs tabela `report_topics`
  no plano do item 5. Relatos novos sao atribuidos via `transform`; re-fit periodico recategoriza.
- **Modelos multilingues pt-BR**: defaults sugeridos `intfloat/multilingual-e5-base` (busca/RAG, usa
  prefixos `query:`/`passage:`) e `paraphrase-multilingual-MiniLM-L12-v2` (BERTopic). Confirmar no
  plano do item 1; manter trocavel por env var.
- **Provedor de LLM (item 6)**: `FALA_GAVEA_LLM_PROVIDER` = `ollama` (default, local) | `anthropic`.
  Anthropic usa SDK oficial `anthropic`, chave em `ANTHROPIC_API_KEY` (env, nunca hardcoded; nao
  commitar), modelo default `claude-haiku-4-5` (o mais barato) via `FALA_GAVEA_ANTHROPIC_MODEL`.
  Verificar `check_secrets.py` antes de commitar para garantir que a chave nao vaze.
- **Mock em testes**: mockar modelo de embedding, ChromaDB e `ILLMClient` (Ollama/Anthropic) em
  unit tests (sem download de modelo, sem servidor, sem chamada de rede). Smoke test real opcional/manual.
- **Permissoes**: busca semantica e similares publicos (como o mapa); chat NL restrito a agent/admin.
- **CONVENTION_1**: todo acesso a ChromaDB/Ollama/BERTopic passa por `infrastructure/` via portas de
  dominio -- nenhum import direto em use cases ou routers.
