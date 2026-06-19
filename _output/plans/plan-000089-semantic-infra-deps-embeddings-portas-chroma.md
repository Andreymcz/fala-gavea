# Plan 000089 | FEATURE -B | 2026-06-19 12:34 | semantic-infra deps embeddings portas chroma | Review: standard
plan_format_version: 1

source: roadmap-000088 -- Wave 0 item 1 (fundacao semantica: deps, registry, chromaclient, portas)

## Brief (verbatim)
roadmap 2 wave 0

## Agent Interpretation

Implementar a fundacao semantica do sistema (Wave 0, item 1 do roadmap-000088):
- Adicionar dependencias de IA ao pyproject.toml: `chromadb`, `sentence-transformers`, `bertopic`
- Criar modulo de config de env vars semanticos
- Criar portas de dominio: `IReportIndexer`, `ISemanticSearchPort`, `ITopicModelPort`
- Criar `EmbeddingProviderRegistry` (D-A: registry proposito->modelo)
- Criar `ChromaSearchClient` em `infrastructure/chromadb/` implementando `IReportIndexer` + `ISemanticSearchPort`
- Testes unitarios com mock do modelo de embedding

## Files

- `pyproject.toml` (modify)
- `src/fala_gavea/infrastructure/embeddings/__init__.py` (create)
- `src/fala_gavea/infrastructure/embeddings/registry.py` (create)
- `src/fala_gavea/infrastructure/chromadb/__init__.py` (create)
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` (create)
- `src/fala_gavea/domain/repositories/semantic_ports.py` (create)
- `tests/unit/infrastructure/__init__.py` (create)
- `tests/unit/infrastructure/test_embedding_registry.py` (create)
- `tests/unit/infrastructure/test_chroma_search_client.py` (create)

## Review

### Perspectives Evaluated

| Tag | Verdict | Notes |
|-----|---------|-------|
| ARCH | Adopted | Todos os acessos a ChromaDB passam por `infrastructure/` via portas (T1/CONVENTION_1). Use cases e routers importam apenas as ABCs de dominio. |
| SEC | Adopted | Nenhuma API key em codigo; chave Anthropic (wave 2) sera via env var. `vectorstore/` gitignored (S2 analogia). |
| OPS | Adopted | Modelos sentence-transformers baixam no primeiro uso (cache HF em `~/.cache/huggingface`). Path do vectorstore via `FALA_GAVEA_VECTORSTORE_PATH`. |
| TEST | Adopted | Embedding model e ChromaDB mockados em unit tests -- sem download de modelo nem servidor em CI. |
| PERF | Deferred | Latencia do encode e sincrona por enquanto; migracao para BackgroundTasks fica para o plano do item 2 se necessario. |

---

## Steps

### Step 1: Adicionar dependencias de IA ao pyproject.toml e criar modulo de config semantico

Adicionar ao `[project.dependencies]` no `pyproject.toml`:
- `chromadb>=0.6` -- vector store
- `sentence-transformers>=3.0` -- modelos de embedding multilingual
- `bertopic>=0.17` -- topic modeling (puxa hdbscan, umap-learn como deps transitivas)

Criar `src/fala_gavea/infrastructure/embeddings/__init__.py` vazio.

Criar `src/fala_gavea/infrastructure/embeddings/registry.py` com `SemanticConfig` (dataclass lendo env vars) e `EmbeddingProviderRegistry`.

`SemanticConfig` le:
- `FALA_GAVEA_EMBED_MODEL_SEARCH` (default: `"intfloat/multilingual-e5-base"`) -- modelo para busca/RAG
- `FALA_GAVEA_EMBED_MODEL_TOPICS` (default: `"paraphrase-multilingual-MiniLM-L12-v2"`) -- backbone BERTopic
- `FALA_GAVEA_VECTORSTORE_PATH` (default: `"vectorstore"`) -- diretorio raiz do vectorstore

`EmbeddingProviderRegistry` mapeia proposito (`"search"`, `"rag"`, `"topics"`) para o nome do modelo (string). `search` e `rag` apontam para o mesmo modelo por padrao (podem divergir depois). Metodo `get_model_name(purpose: str) -> str`.

Nota: o registry nao instancia o modelo de embedding -- isso fica para o ChromaSearchClient que passa o nome ao SentenceTransformer. Isso evita carregar modelos em tempo de import.

- **Files**: `pyproject.toml` (modify), `src/fala_gavea/infrastructure/embeddings/__init__.py` (create), `src/fala_gavea/infrastructure/embeddings/registry.py` (create)
- **References**: `product-design/project/standards.md § Backend`
- **Interface**: exports `SemanticConfig` (dataclass com campos `embed_model_search`, `embed_model_topics`, `vectorstore_path`); `EmbeddingProviderRegistry` com `__init__(config: SemanticConfig)` e `get_model_name(purpose: str) -> str`
- **Verify**: `uv sync` sem erros; `from fala_gavea.infrastructure.embeddings.registry import EmbeddingProviderRegistry` importa sem erro; `EmbeddingProviderRegistry(SemanticConfig()).get_model_name("search")` retorna `"intfloat/multilingual-e5-base"`
- **Tests**: Coberto pelo Step 4 (unit tests do registry)
- [ ] Done

### Step 2: Criar portas de dominio semanticas

Criar `src/fala_gavea/domain/repositories/semantic_ports.py` com as tres ABCs de dominio. Nenhum import de chromadb, sentence-transformers ou bertopic -- apenas stdlib + tipos de dominio.

```python
# IReportIndexer
class IReportIndexer(ABC):
    @abstractmethod
    def index(self, report: Report) -> None: ...
    @abstractmethod
    def delete(self, report_id: str) -> None: ...
    @abstractmethod
    def reindex_all(self, reports: list[Report]) -> None: ...

# ISemanticSearchPort
class ISemanticSearchPort(ABC):
    @abstractmethod
    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]: ...
    @abstractmethod
    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]: ...

# ITopicModelPort
class ITopicModelPort(ABC):
    @abstractmethod
    def topic_of(self, report: Report) -> int: ...
    @abstractmethod
    def list_topics(self) -> list[dict]: ...
    @abstractmethod
    def fit(self, reports: list[Report]) -> None: ...
```

Retorno de `search` e `similar` e `list[tuple[str, float]]` onde o primeiro elemento e o `report_id` e o segundo e o score de similaridade (0.0-1.0).

- **Files**: `src/fala_gavea/domain/repositories/semantic_ports.py` (create)
- **References**: `product-design/project/standards.md § Backend § 4. Repository Pattern`
- **Interface**: exports `IReportIndexer`, `ISemanticSearchPort`, `ITopicModelPort`
- **Verify**: `from fala_gavea.domain.repositories.semantic_ports import IReportIndexer, ISemanticSearchPort, ITopicModelPort` importa sem erro; nenhum import de chromadb ou sentence-transformers no modulo
- **Tests**: N/A (ABCs sem logica implementada)
- [ ] Done

### Step 3: Criar ChromaSearchClient implementando IReportIndexer e ISemanticSearchPort

Criar `src/fala_gavea/infrastructure/chromadb/__init__.py` vazio.

Criar `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`:

- Classe `ChromaSearchClient(IReportIndexer, ISemanticSearchPort)`.
- Construtor recebe `config: SemanticConfig`. Instancia internamente `chromadb.PersistentClient(path=config.vectorstore_path)` e `SentenceTransformer(config.embed_model_search)`.
- Colecao ChromaDB: `falagavea_reports_search` (obtida via `get_or_create_collection`).
- `index(report)`: encode `report.text` com o SentenceTransformer; adiciona ao ChromaDB com `id=report.id`, `document=report.text`, `embedding=<encoded>`, `metadata={"lat": report.lat, "lon": report.lon, "urgency": report.urgency.value, "report_type_id": report.report_type_id}`.
- `delete(report_id)`: deleta o documento da colecao por id.
- `reindex_all(reports)`: deleta a colecao inteira e re-indexa todos os relatos em batch (para backfill).
- `search(query, n)`: encode query; chama `collection.query(query_embeddings=[...], n_results=n)`; converte distancias ChromaDB (L2) para scores (1 / (1 + dist)).
- `similar(report_id, n)`: busca o embedding do report_id na colecao; usa como query; exclui o proprio report_id do resultado.

Nota de prefixo multilingual-e5: o modelo `intfloat/multilingual-e5-base` espera prefixo `"query: "` para queries e `"passage: "` para documentos. Adicionar essa logica como metodo privado `_encode_passage(text)` / `_encode_query(text)`.

- **Files**: `src/fala_gavea/infrastructure/chromadb/__init__.py` (create), `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` (create)
- **References**: `product-design/project/standards.md § Backend § 2. Layer Boundaries`, `product-design/project/constitution.md T1`
- **Depends on**: Step 1, Step 2
- **Interface**: exports `ChromaSearchClient(config: SemanticConfig)` implementando `IReportIndexer` + `ISemanticSearchPort`
- **Verify**: importa sem erro; `ChromaSearchClient` e subclasse de ambas as ABCs (`issubclass(ChromaSearchClient, IReportIndexer)` True)
- **Tests**: Coberto pelo Step 4 (unit com mock de SentenceTransformer e chromadb)
- [ ] Done

### Step 4: Testes unitarios (registry + ChromaSearchClient com mocks)

Criar `tests/unit/infrastructure/__init__.py` vazio.

Criar `tests/unit/infrastructure/test_embedding_registry.py`:
- `test_default_search_model`: `EmbeddingProviderRegistry(SemanticConfig()).get_model_name("search")` retorna `"intfloat/multilingual-e5-base"`
- `test_default_topics_model`: retorna `"paraphrase-multilingual-MiniLM-L12-v2"`
- `test_rag_same_as_search_by_default`: `get_model_name("rag") == get_model_name("search")`
- `test_env_override`: com `FALA_GAVEA_EMBED_MODEL_SEARCH=custom-model`, retorna `"custom-model"`

Criar `tests/unit/infrastructure/test_chroma_search_client.py` usando `unittest.mock.patch`:
- `test_index_calls_collection_add`: mockar `chromadb.PersistentClient` e `SentenceTransformer`; chamar `index(report)`; verificar que `collection.add()` e chamado com o `report.id` como id
- `test_search_returns_list_of_tuples`: mockar query result do chromadb (ids=[[id1]], distances=[[0.5]]); verificar que `search("query")` retorna `[("id1", score)]` onde score = 1/(1+0.5)
- `test_index_failure_propagates`: sem suppressao aqui -- a tolerancia a falha fica no use case (Step 2 do plan-000090)
- `test_similar_excludes_self`: mockar resultado que inclui o proprio report_id; verificar que ele e excluido

- **Files**: `tests/unit/infrastructure/__init__.py` (create), `tests/unit/infrastructure/test_embedding_registry.py` (create), `tests/unit/infrastructure/test_chroma_search_client.py` (create)
- **Depends on**: Step 1, Step 2, Step 3
- **Verify**: `uv run pytest tests/unit/infrastructure/ -v` passa sem erros; sem download de modelos reais (mocks garantem isolamento)
- **Tests**: N/A (este step eh o teste)
- [ ] Done

---

## Commit Message

```
feat(semantic): Add AI deps, embedding registry, domain ports, ChromaSearch

Wave 0 item 1 of roadmap-000088: foundation for semantic spaces.
- chromadb, sentence-transformers, bertopic added to pyproject.toml
- EmbeddingProviderRegistry maps purpose -> model name (env-var configurable)
- Domain ports: IReportIndexer, ISemanticSearchPort, ITopicModelPort
- ChromaSearchClient implements IReportIndexer + ISemanticSearchPort
- Unit tests with mocked SentenceTransformer and chromadb

Plan: plan-000089
```
