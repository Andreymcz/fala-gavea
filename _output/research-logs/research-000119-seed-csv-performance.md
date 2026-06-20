# Research 000119 | fala-gavea | 2026-06-20 23:23 UTC | Seed CSV Performance: Lentidão e Alto Consumo de Memória
tags: performance, chromadb, sentence-transformers, seed, architecture

## User Brief

> investigar porque o seed de relatos em csv esta demorando tanto e usando mta memoria. o servidor esta usando mais que 4GB

## Agent Interpretation

Investigação das causas de lentidão e consumo excessivo de memória (>4GB) durante o processo de seed de relatos via CSV, cobrindo tanto o script CLI (`scripts/seed_relatos.py`) quanto o endpoint de upload (`POST /seed/relatos`).

## Files Reviewed

- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`
- `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py`
- `src/fala_gavea/presentation/api/routers/seed.py`
- `src/fala_gavea/presentation/api/dependencies.py`
- `scripts/seed_relatos.py`
- `src/fala_gavea/domain/repositories/semantic_ports.py`

---

## Q&A Log

### Q1

**Pergunta:** Por que o seed de relatos em CSV demora tanto e usa mais de 4GB de memória?

**Resposta:**

Há dois caminhos de seed e ambos têm problemas distintos:

---

### Caminho A — `scripts/seed_relatos.py` (CLI)

O script envia **10.000 requisições HTTP individuais** para `POST /reports/`, uma por relato. Cada requisição:
1. Faz uma chamada `SentenceTransformer.encode(text)` — um forward pass individual no modelo `multilingual-e5-base` (~500MB).
2. Faz uma chamada `collection.add()` ao ChromaDB — que reconstrói/sincroniza incrementalmente o índice HNSW.

Resultado: 10.000 forward passes separados + 10.000 escritas incrementais no ChromaDB + overhead de 10.000 round-trips HTTP.

---

### Caminho B — `POST /seed/relatos` (upload CSV via API)

O CSV é carregado uma vez, mas `BulkCreateReports.execute()` ainda itera linha a linha e chama `indexer.index(report)` para cada relato individualmente:

```python
# bulk_create_reports.py, linhas 114-118
if indexer is not None:
    try:
        indexer.index(report)  # ← chamada individual por relato
```

E `ChromaSearchClient.index()` faz:
```python
def index(self, report: Report) -> None:
    embedding = self._encode_passage(report.text)  # encode individual
    self._collection.add(...)                       # add individual
```

Para N relatos = N forward passes sem batching + N add() separados ao ChromaDB.

---

### Causa raiz adicional: `reindex_all` também não faz batching correto

O método `reindex_all()` foi identificado como "já existente com batching", mas na verdade ele usa uma list comprehension que ainda chama `_encode_passage` individualmente:

```python
embeddings = [self._encode_passage(r.text) for r in reports]  # linha 66 — N forward passes!
```

Ele faz batching apenas no `collection.add()` (uma chamada), mas não no encode. É o mesmo problema.

---

### Por que >4GB de memória?

1. **Modelo em memória**: `multilingual-e5-base` ocupa ~500MB só para os pesos.
2. **Tensores intermediários acumulados**: 10k chamadas `encode()` individuais alocam buffers de ativação para cada inferência. O GC do Python não libera tensores PyTorch entre chamadas de forma determinística — eles acumulam.
3. **Corpus de strings em memória**: o router lê o CSV inteiro para memória antes de processar (`file.file.read()` → `csv.DictReader`). Para CSVs grandes, o corpus de texto fica na RAM junto com os embeddings gerados.
4. **ChromaDB HNSW**: o índice vetorial cresce na RAM a cada `add()` incremental; para 10k+ documentos, o HNSW pode ocupar centenas de MB a mais.

---

## Recomendações

### 1. [ALTA] Adicionar `index_many()` ao `ChromaSearchClient` com encode em batch

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
            {"lat": r.lat, "lon": r.lon, "urgency": r.urgency.value,
             "report_type_id": r.report_type_id}
            for r in reports
        ],
    )
```

- Adicionar `index_many` à interface `IReportIndexer` em `semantic_ports.py`.
- **Também corrigir `reindex_all`** para usar `self._model.encode(list_of_texts, batch_size=64)` em vez da list comprehension que chama `_encode_passage` individualmente.

### 2. [ALTA] Modificar `BulkCreateReports.execute()` para deferir indexação em chunks

Coletar todos os `Report` criados e chamar `index_many` por chunk no final, em vez de `index()` por linha:

```python
pending_index: list[Report] = []
CHUNK = 500

# ... dentro do loop de rows:
report_repo.save(report)
inserted += 1
pending_index.append(report)

if len(pending_index) >= CHUNK:
    if indexer is not None:
        try:
            indexer.index_many(pending_index)
        except Exception as exc:
            _log.error("index_many failed for %d reports: %s", len(pending_index), exc)
    pending_index.clear()

# ... após o loop:
if pending_index and indexer is not None:
    try:
        indexer.index_many(pending_index)
    except Exception as exc:
        _log.error("index_many failed for %d reports: %s", len(pending_index), exc)
```

O `chunk_size=500` limita o pico de memória no passo de encoding independentemente do tamanho do CSV.

### 3. [MÉDIA] Documentar e tratar a janela de inconsistência SQL ↔ ChromaDB

Com indexação deferida ao final, relatos criados com sucesso no SQL mas que falham no indexing ficam "fantasmas" — visíveis via REST mas invisíveis na busca semântica. Mitigação:
- Logar IDs não-indexados em nível ERROR com detalhes suficientes para um operador rodar `reindex_all`.
- Considerar adicionar `index_failed: bool` na resposta `SeedRelatosResponse`.

### 4. [MÉDIA] Atualizar `scripts/seed_relatos.py` para usar o endpoint CSV

Para volumes acima de ~500 relatos, o script deve usar `POST /seed/relatos` (upload CSV) em vez de 10k requisições individuais. Adicionar aviso no `--help` e detectar `--count > 500` para recomendar o endpoint bulk. **Atenção:** o endpoint CSV requer token de admin, não citizen.

### 5. [BAIXA] Corrigir `reindex_all` isoladamente (mesma passagem que rec. 1)

Substituir a list comprehension por uma chamada `encode()` vetorizada:
```python
# antes:
embeddings = [self._encode_passage(r.text) for r in reports]
# depois:
embeddings = self._model.encode(
    [f"passage: {r.text}" for r in reports], batch_size=64
).tolist()
```

---

## Resumo de Recomendações

| Prioridade | Ação | Arquivo(s) |
|-----------|------|-----------|
| ALTA | Adicionar `index_many()` com encode batched ao `ChromaSearchClient` + interface | `chroma_search_client.py`, `semantic_ports.py` |
| ALTA | Modificar `BulkCreateReports` para usar `index_many` em chunks de 500 | `bulk_create_reports.py` |
| MÉDIA | Tratar inconsistência SQL↔ChromaDB na falha de indexação bulk | `bulk_create_reports.py`, `seed_schemas.py` |
| MÉDIA | Atualizar `scripts/seed_relatos.py` para usar endpoint CSV em bulk | `scripts/seed_relatos.py` |
| BAIXA | Corrigir encode loop em `reindex_all` | `chroma_search_client.py` |
