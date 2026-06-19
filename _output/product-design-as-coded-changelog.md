# Product Design As-Coded Changelog

### v4 — 2026-06-19
- **Added**: §3 BERTopic topic modeling — GET /reports/topics endpoint, BERTopicClient, GetTopicsForReports use case, ITopicModelPort.infer_topics()
- **Changed**: §1 Platform Purpose — endpoint count updated to 17; §4 Permission Model — GET /reports/topics auth-required
- **Source**: agent (post-skill)
- **Plan**: plan-000099

### v3 — 2026-06-19
- **Added**: §3 RAG chat NL assistant (ILLMClient, AnswerWithRag, POST /nl/chat), LLM factory, §11 LLM env vars
- **Source**: agent (post-skill)
- **Plan**: plan-000100

### v2 — 2026-06-19
- **Added**: §11 Deployment & Infrastructure (Dockerfile, railway.json, /health, CHROMA_DATA_DIR, Ollama graceful degradation)
- **Source**: agent (post-skill)
- **Plan**: plan-000096
