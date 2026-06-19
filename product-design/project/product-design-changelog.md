# AS-CODED CHANGELOG — fala-gavea

### v1 -- 2026-06-19
- **Added**: Semantic AI foundation (Wave 0): deps chromadb/sentence-transformers/bertopic, domain ports IReportIndexer/ISemanticSearchPort/ITopicModelPort, EmbeddingProviderRegistry, ChromaSearchClient
- **Source**: agent (post-skill)
- **Plan**: plan-000089

### v2 -- 2026-06-19
- **Added**: Ingestion hook (Wave 0): IReportIndexer injected into CreateReport; get_report_indexer() singleton in dependencies.py; reports router updated; backfill_semantic.py script
- **Source**: agent (post-skill)
- **Plan**: plan-000090

### v3 -- 2026-06-19
- **Added**: Semantic search endpoints (Wave 1): public GET /reports/search and GET /reports/{id}/similar; use cases SearchReports + FindSimilarReports; get_semantic_search_port() dependency reusing the ChromaSearchClient singleton; ReportSearchResult schema (ReportResponse + score)
- **Source**: agent (post-skill)
- **Plan**: plan-000094

### v4 -- 2026-06-19
- **Added**: RAG chat NL assistant (Wave 2): ILLMClient domain port; infrastructure/llm/ package (OllamaAdapter, AnthropicClient, factory); AnswerWithRag use case with pt-BR system prompt and semantic context injection; POST /nl/chat (agent+admin); get_llm_client() dependency; anthropic>=0.50; FALA_GAVEA_LLM_PROVIDER / ANTHROPIC_API_KEY / FALA_GAVEA_ANTHROPIC_MODEL env vars
- **Source**: agent (post-skill)
- **Plan**: plan-000100
