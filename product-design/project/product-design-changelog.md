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
