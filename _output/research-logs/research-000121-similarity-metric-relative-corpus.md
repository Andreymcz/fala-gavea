# Research 000121 | fala-gavea | 2026-06-21 00:15 UTC | Métrica de similaridade relativa ao corpus
tags: semantic-search, similarity, chromadb, statistics, ux

## User Brief

> é possivel, dado um relato, ter uma metrica que diz que eles possuem relatos muito parecidos, em comparacao com o resto do universo de relatos ?

## Agent Interpretation

A pergunta é sobre computar uma métrica **relativa ao corpus** que responda: "estes dois relatos são mais similares do que X% de todos os pares de relatos". Atualmente o projeto retorna um score absoluto (`1/(1+l2_dist)` via ChromaDB), mas não contextualiza esse score em relação à distribuição do corpus.

## Files Consulted

- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`
- `product-design/project/product-design-as-coded.md`

---

## Q&A Log

**Q1:** É possível, dado um relato, ter uma métrica que diz que eles possuem relatos muito parecidos, em comparação com o resto do universo de relatos?

**A1:**

Sim, é plenamente viável. O que você precisa é de um **score relativo ao corpus**, e a abordagem mais prática dado o stack atual é o **percentil sobre amostra aleatória de pares**.

### Como funciona

O score atual (`1/(1+l2_dist)`) é **absoluto** — não diz nada sobre se 0.87 é alto ou baixo para este corpus. A ideia é criar uma distribuição de referência:

1. Na inicialização do servidor (ou a cada N horas), amostrar K pares aleatórios do corpus (K = 3000–5000)
2. Computar os scores de todos esses pares
3. Guardar a distribuição em memória (array numpy ou lista para `bisect`)
4. Para qualquer par (A, B), expressar `score(A, B)` como percentil nessa distribuição

**Resultado legível**: `similarity_percentile: 0.93` → "este par é mais similar do que 93% de todos os pares do corpus → provável duplicata"

### Abordagens avaliadas

| Abordagem | Custo por request | Interpretabilidade | Recomendação |
|---|---|---|---|
| **1. Percentil (amostra aleatória)** | O(log K) — <1ms | Alta ("mais similar que X%") | ✅ Principal |
| **2. Z-score** | O(1) após pre-cálculo | Média (requer conhecimento estatístico) | ✅ Complementar (grátis) |
| **3. kNN local baseline** | ~50-80ms (2 queries ChromaDB) | Alta ("incomum localmente") | ✅ Opt-in (param extra) |
| **4. UMAP/HDBSCAN** | Batch only (segundos) | Alta (clusterização) | ❌ Diferir |

### Detalhe da abordagem 1 (recomendada)

```python
class CorpusSimilarityBaseline:
    def __init__(self):
        self._sorted_scores: list[float] = []

    def warm_up(self, collection, k: int = 5000):
        # sample k random pairs, compute scores, sort
        ...

    def percentile(self, score: float) -> float:
        # bisect_left → index / len → percentile 0.0–1.0
        import bisect
        idx = bisect.bisect_left(self._sorted_scores, score)
        return idx / len(self._sorted_scores)
```

Warm-up: < 2s para 10k relatos com K=5000.  
Por request: O(log K) ≈ sub-milissegundo.

### Detalhe da abordagem 3 (kNN local baseline)

Para o caso em que o corpus é heterogêneo (há tópicos densos: "buraco na rua" aparece muito, "deslizamento" é raro), o percentil global pode ser enganoso: dois relatos de "buraco na rua" pouco similares podem ter percentil alto simplesmente porque buracos são o tópico dominante.

A abordagem kNN computa: "esta similaridade é alta *para a região local do espaço semântico*?"

```
is_locally_unusual = score(A,B) > max(avg_knn_score(A), avg_knn_score(B))
```

Custo: 2 queries ao ChromaDB por request (~50ms), opt-in via `?include_local_baseline=true`.

### Complementaridade

Expor os dois campos no response de `GET /reports/{id}/similar`:

```json
{
  "id": "...",
  "score": 0.87,
  "similarity_percentile": 0.93,
  "similarity_zscore": 2.4
}
```

- **UX/frontend**: mostrar `similarity_percentile` como porcentagem ("mais similar que 93% dos pares")
- **Automação futura (deduplicação)**: usar `similarity_zscore > 2.5` como threshold

### Onde implementar (arquitetura)

`CONVENTION_1` do projeto manda que toda lógica semântica passe pelo `infrastructure/`. O lugar certo é:

```
src/fala_gavea/infrastructure/chromadb/
    chroma_search_client.py       (existente)
    corpus_similarity_baseline.py (novo)
```

Injetar via FastAPI dependency injection (mesmo padrão do `get_semantic_search_port()`), não como singleton — assim testes podem injetar versão com seed fixo.

### Refresh do baseline

A cada 4–6 horas via FastAPI background task ou APScheduler, para o baseline acompanhar o crescimento do corpus. Configurável via env var `FALA_GAVEA_SIMILARITY_BASELINE_REFRESH_HOURS`.

### Degradação graciosa

Se o ChromaDB não estiver disponível no warm-up, o servidor não deve falhar — apenas serve o score bruto sem o percentil (campo omitido ou `null`), logando um WARNING.

---

## Recommendations Summary

1. **[ALTO]** Implementar `CorpusSimilarityBaseline` em `infrastructure/chromadb/corpus_similarity_baseline.py` usando amostra aleatória de K=5000 pares; expor `similarity_percentile` (0.0–1.0) e `similarity_zscore` no response de `/reports/{id}/similar` e `/reports/search`
2. **[ALTO]** Injetar via FastAPI DI (não singleton) para testabilidade; degradação graciosa se ChromaDB indisponível no warm-up
3. **[MÉDIO]** Adicionar `is_locally_unusual` (abordagem kNN) como campo opt-in via query param `?include_local_baseline=true` — custo de 2 queries ChromaDB, mas correto para corpus heterogêneo
4. **[MÉDIO]** Agendar refresh do baseline a cada N horas via FastAPI lifespan/background task; expor intervalo em env var
5. **[BAIXO]** Diferir UMAP/HDBSCAN (abordagem 4) — requer infraestrutura de jobs batch inexistente; revisitar quando houver dashboard analítico para admin
