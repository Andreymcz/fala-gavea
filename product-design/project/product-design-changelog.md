# AS-CODED CHANGELOG — fala-gavea

### v1 -- 2026-06-19
- **Added**: Semantic AI foundation (Wave 0): deps chromadb/sentence-transformers/bertopic, domain ports IReportIndexer/ISemanticSearchPort/ITopicModelPort, EmbeddingProviderRegistry, ChromaSearchClient
- **Source**: agent (post-skill)
- **Plan**: plan-000089

### v2 -- 2026-06-19
- **Added**: Ingestion hook (Wave 0): IReportIndexer injected into CreateReport; get_report_indexer() singleton in dependencies.py; reports router updated; backfill_semantic.py script
- **Source**: agent (post-skill)
- **Plan**: plan-000090
