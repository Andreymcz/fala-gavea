# QA Log | Plan 000094 | 2026-06-19 14:30 UTC | semantic-search + similar-reports wave 1 planning session

**Brief**: roadmap 2 wave 1 -- planejamento da Wave 1 do roadmap-000088 (espacos semanticos IA): gerou plan-000094 cobrindo os itens 3 (semantic-search) e 4 (similar-reports) num unico plano.

---

## Q1
/plan roadmap 2 wave 1

## A1
Interpretou "roadmap 2 wave 1" como a Wave 1 do roadmap-00002 (roadmap-000088, wave2-espacos-semanticos-ia). Carregou o roadmap e identificou a Wave 1 com dois itens paralelos: item 3 (semantic-search, `GET /reports/search`) e item 4 (similar-reports, `GET /reports/{id}/similar`).

Verificou o estado de partida no codigo:
- Wave 0 ja implementada: hook de indexacao em `CreateReport`, `scripts/backfill_semantic.py`, `EmbeddingProviderRegistry`, e portas de dominio em `semantic_ports.py`.
- **`ISemanticSearchPort` ja existe e `ChromaSearchClient` ja implementa `search()` e `similar()`** (inclusive a exclusao do proprio relato em `similar()`) -> Wave 1 e essencialmente wiring (use cases + endpoints + DI + schema + testes), nao trabalho de algoritmo.

Leu os padroes existentes: `dependencies.py` (singleton `get_report_indexer` retorna `ChromaSearchClient`, que implementa ambas as portas), `routers/reports.py` (ordem `/geojson` antes de `/{id}`; `get_report` publico/projecao `ReportResponse`/404), `report_repository.py` (`find_by_id`), `schemas/report.py`, e `conftest.py` (fixtures + `dependency_overrides`).

## Q2
[AskUserQuestion] Estrutura: um plano combinado ou dois planos separados?

## A2
Usuario escolheu **um plano combinado** (recomendado): os dois itens editam os mesmos arquivos (`routers/reports.py`, `dependencies.py`, `schemas/report.py`), entao separa-los em sessoes paralelas geraria conflito de merge. A porta de busca ja esta implementada, reduzindo o escopo.

Reservou o ID 000094 e gerou **plan-000094** (9 steps, Review: light):
1. Schema `ReportSearchResult` (= `ReportResponse` + `score`)
2. Use case `SearchReports` (hidrata por id, preserva score, pula ids ausentes no SQLite)
3. Use case `FindSimilarReports` (404 se base ausente, hidrata vizinhos)
4. Dependency `get_semantic_search_port()` reaproveitando o singleton `ChromaSearchClient`
5. Endpoints publicos `GET /reports/search` (registrado **antes** de `/{id}`) e `GET /reports/{id}/similar`; 503 se ChromaDB indisponivel
6-8. Testes unitarios (ambos use cases) + testes de integracao com fake `ISemanticSearchPort` (sem carregar modelo/ChromaDB)
9. Suite completa + ruff + pyright

Dois pontos de correcao destacados no plano: (a) `/search` deve ser registrado antes de `/{id}` senao FastAPI o casa como id; (b) o vectorstore pode conter ids cujo `Report` foi removido do SQLite -> use cases pulam ids nao-hidrataveis.
