# Research 000122 | fala-gavea | 2026-06-21 12:46 UTC | Reduce Memory Usage — Railway Deployment

tags: memory-optimization, railway, sentence-transformers, chromadb, bertopic, infrastructure

**User brief:** how to reduce memory usage. our railway app is using 2GB RAM without any active usage. this will give us an estimate usage of $22. which is unacceptable

**Agent interpretation:** Identify the root causes of ~2GB idle RAM usage in the fala-gavea FastAPI deployment on Railway, and recommend actionable strategies to bring it under 512MB–1GB (target: <$10/month Railway tier).

**Files reviewed:**
- `src/fala_gavea/presentation/api/main.py`
- `src/fala_gavea/presentation/api/dependencies.py`
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`
- `src/fala_gavea/infrastructure/topics/bertopic_client.py`
- `src/fala_gavea/infrastructure/embeddings/registry.py`
- `pyproject.toml`
- `Dockerfile`

---

## Q&A Log

**Q1: How do we reduce idle RAM from ~2GB on Railway to an acceptable level?**

### Root causes identified

The idle ~2GB is explained by five concurrent consumers loaded at startup or on first request, then held for the process lifetime:

| Consumer | Approx. RAM |
|---|---|
| `multilingual-e5-base` (SentenceTransformer) | 450–700 MB |
| `paraphrase-multilingual-MiniLM-L12-v2` (BERTopicClient) | 200–300 MB |
| PyTorch runtime (shared, C extensions) | 200–400 MB |
| ChromaDB PersistentClient + HNSW index | 50–200 MB |
| BERTopic deps (UMAP, HDBSCAN, scikit-learn) | 100–200 MB |
| Python / FastAPI / SQLAlchemy baseline | ~50–100 MB |

Both `_indexer_instance` (ChromaSearchClient) and `_topic_model_instance` (BERTopicClient) are lazy singletons that initialize on first request and are never released. The Dockerfile pre-downloads only `multilingual-e5-base`, so MiniLM downloads at first `/reports/topics` call, but both models then stay resident forever.

The two SentenceTransformer models are kept in separate singleton instances because `EmbeddingProviderRegistry` only maps purpose strings to model _names_, not to loaded model objects — so each client constructs its own `SentenceTransformer(...)` independently.

BERTopic is additionally problematic: `infer_topics()` runs `fit_transform()` on every request (full UMAP + HDBSCAN re-training from scratch), which is architecturally incorrect for a topic model but also means UMAP/HDBSCAN imports are brought in on first `/topics` call and never released.

---

## Recommendations Summary

### HIGH priority

**R1 — Force CPU-only PyTorch**
Set `torch` to the CPU wheel in the Dockerfile:
```dockerfile
RUN uv sync --frozen --no-dev --extra-index-url https://download.pytorch.org/whl/cpu
```
Or pin in `pyproject.toml` via `[tool.uv.sources]`. CUDA shared libraries add 200–600 MB of runtime overhead on Railway CPU-only machines even when not used. Zero application risk, build-only change.

**R2 — Downgrade `multilingual-e5-base` → `multilingual-e5-small`**
Set env var on Railway: `FALA_GAVEA_EMBED_MODEL_SEARCH=intfloat/multilingual-e5-small`
Update Dockerfile line 26: change `multilingual-e5-base` → `multilingual-e5-small`.
Expected saving: 250–400 MB. Quality impact: ~2–4 MTEB retrieval points — negligible for short Portuguese urban safety texts.
**⚠ Requires re-indexing ChromaDB** after deploy: embedding dimensions change from 768 to 384. Run `reindex_all()` or clear and re-seed the collection.

**R3 — Unify the two SentenceTransformer models into one shared instance**
Promote `EmbeddingProviderRegistry` (`src/fala_gavea/infrastructure/embeddings/registry.py`) from a name-registry to a model-instance registry: lazy-load and cache the actual `SentenceTransformer` objects. Update `BERTopicClient.__init__` to accept a pre-loaded `SentenceTransformer` instance rather than constructing its own. Inject the shared instance through `dependencies.py`.
Expected saving: eliminates the full MiniLM model load (~200–300 MB) plus its independent PyTorch model graph allocation.

**Combined effect of R1 + R2 + R3: ~700–1,100 MB saved → idle RAM of ~600–900 MB.**

### MEDIUM priority

**R4 — Replace BERTopic with TF-IDF keyword extraction**
BERTopic adds MiniLM + UMAP/HDBSCAN + scikit-learn (~300–500 MB), and its current usage is architecturally incorrect (re-trains on every request). Replace with `sklearn.feature_extraction.text.TfidfVectorizer` (no new model, millisecond latency, reproducible results). Alternative: `KeyBERT` reusing the existing search model — better semantic quality, still no second model. This would also allow removing `bertopic` from `pyproject.toml` entirely.

**R5 — Tune ChromaDB HNSW settings**
When creating the collection, pass:
```python
{"hnsw:space": "cosine", "hnsw:construction_ef": 64, "hnsw:M": 8}
```
For a small Gávea-scoped corpus, this halves HNSW index memory with no meaningful recall loss. Expected saving: 20–80 MB.

**R6 — Explicit `--workers 1` in Dockerfile CMD**
Add `--workers 1` to the uvicorn command. Each additional worker duplicates all model allocations. The current CMD doesn't specify workers, which defaults to 1, but making it explicit prevents accidental multi-worker misconfiguration in CI/CD.

### LOW priority

**R7 — Replace BERTopic with TF-IDF + K-means**
Use `sklearn.feature_extraction.text.TfidfVectorizer` (Portuguese stop-words, unigrams+bigrams) + `KMeans(n_clusters=K, random_state=42)`. scikit-learn is already a transitive dep of BERTopic — no new package needed. Output preserves `{topic_id, terms, count}` schema. Deterministic, reproducible topic IDs. <100ms for <5,000 documents. Replace `BERTopicClient` with a ~50-line `TopicsClient`. Remove `bertopic` from `pyproject.toml`. If keyword quality proves poor, layer in KeyBERT-style extraction reusing the existing `e5-small` singleton (no second model).

---

## Cost Projection

| Scenario | Est. idle RAM | Railway cost est. |
|---|---|---|
| Current (baseline) | ~2 GB | ~$22/month |
| R1 only (CPU torch) | ~1.4–1.8 GB | ~$15–18/month |
| R1 + R2 (smaller model) | ~1.0–1.4 GB | ~$10–15/month |
| R1 + R2 + R3 (unified model) | ~600–900 MB | ~$5–10/month |
| R1 + R2 + R3 + R4 (remove BERTopic) | ~400–600 MB | ~$5/month |
