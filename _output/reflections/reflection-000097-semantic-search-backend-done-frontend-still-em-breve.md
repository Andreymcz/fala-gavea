# Reflection 000097 | 2026-06-19 18:25 UTC | semantic search backend done — frontend still em breve

## Artifacts reflected on

- [plan-000090 — ingestion pipeline / indexação de relatos (Wave 0)](../plans/plan-000090-ingestion-pipeline-indexacao-relatos-backfill.md)
- [plan-000094 — semantic search + similar reports endpoints (Wave 1)](../plans/plan-000094-semantic-search-similar-reports-wave1.md)

## Summary

**plan-000090** wired `IReportIndexer` into `CreateReport` as an optional dependency — index called after save, failures log a warning and never abort report creation. Added `get_report_indexer()` singleton in `dependencies.py` (lazy init, graceful `None` fallback if ChromaDB is unavailable). Created `scripts/backfill_semantic.py` (idempotent, `--force`/`--batch-size` flags). 3 new unit tests; 53 total passed.

**plan-000094** implemented `GET /reports/search?q=…` and `GET /reports/{id}/similar` — both public, backed by `ISemanticSearchPort`. New use cases `SearchReports` and `FindSimilarReports` hydrate vectorstore hits via `IReportRepository.find_by_id`, skip orphan ids, and return `ReportSearchResult` (ReportResponse + score). `get_semantic_search_port()` reuses the `ChromaSearchClient` singleton. 14 new tests (unit + integration with fake port). Deferred findings included no rate limiting, public projection exposing full text/coords/author_id, N+1 hydration, and `n` clamping not documented in OpenAPI.

## Reflection

plan 94 did not implement any frontend feature

## Follow-ups

- The backend endpoints `GET /reports/search` and `GET /reports/{id}/similar` are live, but the frontend still shows "Busca semântica (em breve)" — a Wave 2 plan is needed to wire the UI to these endpoints.
- Which UI surface should carry the semantic search: the existing relatos list page, a dedicated search panel, or both?
- The `/{id}/similar` endpoint is also unexposed in the frontend — deciding where "relatos similares" appears (report detail view?) is an open design question.
