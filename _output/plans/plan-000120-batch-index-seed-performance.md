# DONE | 2026-06-20 23:53 UTC | Plan 000120 | fala-gavea-performance | 2026-06-20 23:43 UTC | Batch Indexing: index_many + BulkCreateReports chunked | Review: light
plan_format_version: 1
source: research-000119

## Brief

Implementar as recomendações de prioridade ALTA da research-000119 para resolver lentidão e consumo excessivo de memória (>4GB) no seed de relatos via CSV:

1. Adicionar `index_many()` batched ao `ChromaSearchClient` e à interface `IReportIndexer`
2. Modificar `BulkCreateReports.execute()` para usar `index_many` em chunks de 500 em vez de `index()` por linha

## Why

O seed atual chama `SentenceTransformer.encode(text)` individualmente para cada relato — N forward passes separados sem batching. Para 10k relatos isso aloca buffers de ativação PyTorch sem liberar entre chamadas, causando consumo cumulativo de RAM >4GB. Adicionalmente, `collection.add()` individual no ChromaDB força rebuild incremental do índice HNSW a cada insert. Com batching, `encode([...], batch_size=64)` agrupa os textos num único forward pass vetorizado, e um único `collection.add()` ao final processa o chunk inteiro.

## Scope

**Modified:**
- `src/fala_gavea/domain/repositories/semantic_ports.py` — adicionar `index_many` à `IReportIndexer`
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` — implementar `index_many` + corrigir `reindex_all`
- `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py` — usar `index_many` em chunks

**Not in scope:** `scripts/seed_relatos.py` (recomendação MÉDIA), inconsistência SQL↔ChromaDB (recomendação MÉDIA).

## Steps

### Step 1 — Adicionar `index_many` à interface `IReportIndexer`
**File:** `src/fala_gavea/domain/repositories/semantic_ports.py`
**Change:** Adicionar método abstrato `index_many` com implementação default (loop sobre `index`) para não quebrar implementações existentes que não precisam de batching (ex: mocks de teste).

```python
@abstractmethod
def index_many(self, reports: list[Report], batch_size: int = 64) -> None:
    """Index multiple reports in a single batched operation."""
    for report in reports:
        self.index(report)
```

> Usando `@abstractmethod` com corpo default (válido em Python ABC): subclasses que não sobrescrevem herdam o loop-fallback; `ChromaSearchClient` sobrescreverá com implementação batched.

**Docs:** N/A

---

### Step 2 — Implementar `index_many` em `ChromaSearchClient` + corrigir `reindex_all`
**File:** `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`

**2a — Adicionar `index_many`:**
```python
def index_many(self, reports: list[Report], batch_size: int = 64) -> None:
    if not reports:
        return
    texts = [f"passage: {r.text}" for r in reports]
    embeddings = self._model.encode(
        texts, batch_size=batch_size, show_progress_bar=False
    ).tolist()
    self._collection.add(
        ids=[r.id for r in reports],
        documents=[r.text for r in reports],
        embeddings=embeddings,
        metadatas=[
            {
                "lat": r.lat,
                "lon": r.lon,
                "urgency": r.urgency.value,
                "report_type_id": r.report_type_id,
            }
            for r in reports
        ],
    )
```

**2b — Corrigir `reindex_all`** (bônus incluído neste step pois toca o mesmo arquivo):
Substituir a list comprehension em `reindex_all` que chama `_encode_passage` individualmente por uma chamada vetorizada:
```python
# antes (linha 66):
embeddings = [self._encode_passage(r.text) for r in reports]
# depois:
embeddings = self._model.encode(
    [f"passage: {r.text}" for r in reports], batch_size=64, show_progress_bar=False
).tolist()
```

**Docs:** N/A

---

### Step 3 — Modificar `BulkCreateReports.execute()` para indexação em chunks
**File:** `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py`

**Lógica:**
- Acumular `Report` objects criados em `pending_index: list[Report]`
- Chamar `indexer.index_many(pending_index)` a cada `CHUNK_SIZE = 500` relatos ou ao final do loop
- Em caso de falha do `index_many`, logar em nível ERROR os IDs não-indexados (sem abortar — os relatos já foram salvos no SQL)
- Remover a chamada `indexer.index(report)` individual dentro do loop

```python
CHUNK_SIZE = 500

# no execute():
pending_index: list[Report] = []

# ... dentro do loop de rows (após report_repo.save(report)):
pending_index.append(report)
if len(pending_index) >= CHUNK_SIZE:
    if indexer is not None:
        try:
            indexer.index_many(pending_index)
        except Exception as exc:
            _log.error(
                "index_many failed for reports %s: %s",
                [r.id for r in pending_index],
                exc,
            )
    pending_index.clear()

# após o loop:
if pending_index and indexer is not None:
    try:
        indexer.index_many(pending_index)
    except Exception as exc:
        _log.error(
            "index_many failed for reports %s: %s",
            [r.id for r in pending_index],
            exc,
        )
```

**Remover** o bloco `if indexer is not None: indexer.index(report)` dentro do loop (linhas 114-118 do arquivo atual).

**Docs:** N/A

---

### Step 4 — Verificar que mocks de teste ainda compilam
**File:** `tests/` (leitura, sem edição)
Verificar se há implementações de `IReportIndexer` em testes que precisem adicionar `index_many`. Como a interface usa corpo default (Step 1), mocks que herdam de `IReportIndexer` sem sobrescrever `index_many` funcionarão via fallback. Verificar se há algum mock que herda diretamente sem usar o padrão ABC (ex: `MagicMock` — não precisa de mudança).

**Docs:** N/A

---

## Test Plan

- [ ] Iniciar servidor: `uv run uvicorn fala_gavea.presentation.api.main:app --reload`
- [ ] Fazer upload de CSV com ~100 relatos via `POST /seed/relatos` (admin token) e confirmar que todos são inseridos e indexados sem erro
- [ ] Executar `uv run pytest` — todos os testes devem passar
- [ ] Opcional: monitorar uso de memória durante seed com CSV de 1000+ relatos e confirmar que não ultrapassa ~1GB

## Risks

- **`index_many` com corpo default em ABC**: Python permite `@abstractmethod` com corpo. Subclasses que não sobrescrevem chamarão o fallback loop. Se alguma subclass de teste já implementa `index_many` com assinatura diferente, haverá conflito de assinatura — improvável dado que o método não existia antes.
- **Chunk flush assíncrono**: se o servidor receber SIGTERM no meio de um chunk, relatos nesse chunk terão sido salvos no SQL mas não indexados. Mitigação: o log ERROR em nível de IDs permite recovery via `reindex_all`.
