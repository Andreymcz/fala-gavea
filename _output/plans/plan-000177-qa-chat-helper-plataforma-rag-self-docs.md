# QA Log — plan-000177 | Chat-helper da plataforma: RAG sobre self-docs (D-014)

source: plan-000177

## Brief

source:research-000175 Implementar o chat-helper da plataforma (D-014): bounded context próprio com IDocSearchPort/IDocIndexer + ChromaDocSearchClient (coleção falagavea_selfdocs) + AnswerHelpWithRag + POST /nl/help para todos usuários autenticados; chunking por heading com metadata role_visibility (default-deny) e filtro por papel; script reindex_selfdocs offline; reusar factory LLM + contrato 503 + rate-limit; citar fontes (cited_doc_paths)

## Q&A

**Q1:** Como o corpus será armazenado / gerado?

**A1:** Distinção entre geração e armazenamento:
- **Geração**: não há geração nova — o corpus são os artefatos markdown que as skills do SEJA já produzem (`_output/plans`, `_output/research-logs`, `_output/reflections`, `_output/communication`, `product-design/project`). A feature apenas lê e indexa via `scripts/reindex_selfdocs.py` (walk → chunk por heading → classifica role_visibility → embed).
- **Armazenamento**: somente no ChromaDB, na coleção própria `falagavea_selfdocs` (separada de `falagavea_reports_search`, mesmo `PersistentClient` path = `CHROMA_DATA_DIR`/`./chroma_data`). O **texto** do chunk é o campo `documents` do Chroma (sem tabela SQLite — por isso `IDocSearchPort` retorna o texto direto). Metadata por chunk: `source_path`, `doc_type`, `section_title`, `chunk_index`, `role_visibility`. `chroma_data/` é gitignored (artefato derivado).
- **Freshness**: rebuild manual via script (idempotente, `reindex_all` substitui a coleção).

**Decisões de refino tomadas (AskUserQuestion):**
1. **Build do índice**: rodar no **build/startup do container** — copiar `_output/` (subdirs de corpus) + `product-design/` para a imagem e indexar em startup (thread de background, `if_empty`, não bloqueia healthcheck). Resultou no novo **Step 9 (Deploy)**.
2. **Persistência**: confirmado **só no ChromaDB** (como no plano), sem tabela SQLite nem manifesto extra.

## Decisões / Resultado

- Plano `plan-000177` gerado (9 steps, Review: standard) a partir de research-000175 / D-014.
- 5 emendas do plan-reviewer aplicadas (fail-closed role filter, correção do rate-limit per-IP, secret-pattern guard, shared `get_embedding_model()`, mapeamento explícito de campos).
- Step 9 (Deploy) adicionado por refino: corpus na imagem + indexação em startup em background.
