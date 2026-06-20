# Research 000116 | fala-gavea | 2026-06-20 21:46 UTC | Railway restart ao ingerir CSV

tags: deployment, oom, sentence-transformers, chromadb, railway

## User Brief

> logs do railway, parece que o servidor esta reiniciando quando tenta ingerir um csv
>
> [logs colados mostram]: Warning: You are sending unauthenticated requests to the HF Hub → Started server process [5] (restart)

## Agent Interpretation

O servidor Railway reinicia toda vez que alguém faz POST /seed/relatos (ingestão de CSV com relatos). A causa é OOM (Out of Memory) ao baixar e carregar o modelo `intfloat/multilingual-e5-base` (~560MB) do HuggingFace em tempo de execução, pois o Dockerfile não faz o download do modelo durante o build.

## Files

- [src/fala_gavea/infrastructure/chromadb/chroma_search_client.py](src/fala_gavea/infrastructure/chromadb/chroma_search_client.py)
- [src/fala_gavea/infrastructure/embeddings/registry.py](src/fala_gavea/infrastructure/embeddings/registry.py)
- [src/fala_gavea/presentation/api/dependencies.py](src/fala_gavea/presentation/api/dependencies.py)
- [src/fala_gavea/presentation/api/routers/seed.py](src/fala_gavea/presentation/api/routers/seed.py)
- [Dockerfile](Dockerfile)

---

## Q&A Log

**Q1:** Por que o servidor Railway reinicia ao ingerir um CSV?

**A1:** A causa raiz é um crash por OOM (Out of Memory) ao tentar carregar o modelo `intfloat/multilingual-e5-base` (~560MB) do HuggingFace em tempo de execução.

**Evidência nos logs:**
- `Warning: You are sending unauthenticated requests to the HF Hub` — o modelo está sendo baixado do HuggingFace em runtime (não está embutido na imagem Docker)
- `Started server process [5]` imediatamente após — o container foi morto pelo OOM killer e reiniciou (PID mudou de [16] para [5])
- O padrão se repete: boot → servir estático → primeira requisição com indexer → download HF → crash → boot

**Cadeia de código:**
1. `POST /seed/relatos` chama `get_report_indexer()` via FastAPI Depends
2. `get_report_indexer()` instancia `ChromaSearchClient(SemanticConfig())` (primeira vez)
3. `ChromaSearchClient.__init__` chama `SentenceTransformer(config.embed_model_search)` — carrega `intfloat/multilingual-e5-base` (~560MB on disk, 800MB–1.2GB em RAM com buffers PyTorch)
4. O container Railway (tipicamente 512MB–1GB RAM no tier free/hobby) é morto pelo OOM killer

O Dockerfile **não** contém nenhum passo de pré-download do modelo — ele apenas faz `uv sync` e copia o source. O modelo é baixado do zero a cada cold start que aciona o indexer.

---

## Recommendations Summary

### HIGH

**Rec 1 — Trocar para `paraphrase-multilingual-MiniLM-L12-v2` E pré-baixar no Dockerfile (Fix combinado)**

Essa é a única opção que elimina simultaneamente o OOM (modelo menor cabe na RAM do Railway) e o download em runtime (cold-start determinístico).

```dockerfile
# Após o uv sync no Dockerfile:
RUN uv run python -c \
  "from sentence_transformers import SentenceTransformer; \
   SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

E em `registry.py`:
```python
embed_model_search: str = field(
    default_factory=lambda: os.getenv(
        "FALA_GAVEA_EMBED_MODEL_SEARCH", "paraphrase-multilingual-MiniLM-L12-v2"
    )
)
```

**Atenção:** embeddings existentes no ChromaDB são incompatíveis (dimensão muda de 768 para 384). Wipe + re-ingest obrigatório após o deploy.

Trade-off: qualidade semântica menor, mas MiniLM multilingual é adequado para o volume e domínio do projeto (relatos de segurança urbana em bairro restrito).

**Rec 2 — Verificar comportamento quando `get_report_indexer()` retorna `None`**

O `except Exception` em `dependencies.py` silencia falhas de init. Routers que recebem o indexer como dependency devem retornar HTTP 503 com corpo claro (`{"detail": "semantic search unavailable"}`) em vez de propagar `AttributeError` como 500.

### MEDIUM

**Rec 3 — Adicionar `FALA_GAVEA_DISABLE_SEMANTIC` como escape hatch documentado**

Guardar em `get_report_indexer()` via env var para que operadores possam desligar o ChromaDB sem redeploy. Documentar no README e na config do Railway.

**Rec 4 — Montar o cache HF como volume persistente no Railway**

Mesmo com pré-download na imagem, montar `/app/.hf_cache` como volume persistente elimina re-download se o layer cache da imagem for perdido. Configurar `HF_HOME=/app/.hf_cache`.

### LOW

**Rec 5 — Configurar memory limit explícito no Railway e health check que verifica ChromaDB**

Torna o consumo de recursos visível e dá ao Railway sinal para reiniciar controladamente antes do OOM killer agir.
