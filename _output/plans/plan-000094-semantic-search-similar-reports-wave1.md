# DONE | 2026-06-19 15:02 UTC | Plan 000094 | FEATURE -B | 2026-06-19 14:27 | semantic-search + similar-reports endpoints (roadmap2 wave1) | Review: light
plan_format_version: 1

source: roadmap-000088 -- Wave 1 (item 3 semantic-search + item 4 similar-reports)

## Brief (verbatim)
roadmap 2 wave 1

## Agent Interpretation

Implementar a **Wave 1** do roadmap-000088 (espacos semanticos / IA), combinando os dois itens
de busca num unico plano porque ambos editam os mesmos arquivos (`routers/reports.py`,
`dependencies.py`, `schemas/report.py`) e dependem da mesma porta -- separa-los em planos
paralelos geraria conflito de merge. Decisao do usuario: plano combinado.

- **Item 3 -- semantic-search**: `GET /reports/search?q=<texto>&n=10` -- busca semantica;
  consulta `ISemanticSearchPort.search`, hidrata cada `Report` por id, retorna lista com `score`.
  Publico (alinhado a `GET /reports/geojson`).
- **Item 4 -- similar-reports**: `GET /reports/{id}/similar?n=5` -- vizinhos semanticos de um
  relato; consulta `ISemanticSearchPort.similar`, 404 se o relato base nao existe, exclui o
  proprio relato (a porta ja exclui). Publico.

Estado de partida favoravel: `ISemanticSearchPort` ja existe em
`domain/repositories/semantic_ports.py` com `search()` e `similar()`, e `ChromaSearchClient`
(`infrastructure/chromadb/chroma_search_client.py`) **ja implementa ambos** -- inclusive a
exclusao do proprio relato em `similar()`. Wave 0 (itens 1 e 2) esta implementada no codigo
(hook de indexacao em `CreateReport`, `backfill_semantic.py`, registry de embeddings). Portanto
esta Wave e essencialmente: use cases + endpoints + DI + schema + testes. Nenhuma chamada direta
a ChromaDB fora de `infrastructure/` (CONVENTION_1).

## Files

- `src/fala_gavea/application/use_cases/reports/search_reports.py` (create)
- `src/fala_gavea/application/use_cases/reports/find_similar_reports.py` (create)
- `src/fala_gavea/presentation/api/dependencies.py` (modify)
- `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- `src/fala_gavea/presentation/schemas/report.py` (modify)
- `tests/unit/application/test_search_reports.py` (create)
- `tests/unit/application/test_find_similar_reports.py` (create)
- `tests/test_reports_semantic.py` (create)

## Review

### Perspectives Evaluated

| Tag | Verdict | Notes |
|-----|---------|-------|
| ARCH | Adopted | Use cases recebem `ISemanticSearchPort` (porta de dominio) + `IReportRepository`; nenhum import de chromadb em application/presentation. Dependencia application -> domain apenas (CONVENTION_1, standards § Layer Boundaries). |
| API | Adopted | `GET /reports/search` deve ser registrado **antes** de `GET /{id}` no router senao FastAPI casa `/search` com `/{id}` (mesmo motivo de `/geojson` vir antes). `/{id}/similar` nao conflita. Ambos publicos (sem `get_current_user`), alinhado a `/geojson` e ao roadmap (busca/similares publicos). |
| TEST | Adopted | `ISemanticSearchPort` mockavel (fake retornando tuplas fixas) -> testes sem carregar modelo de embedding nem ChromaDB. Override via `app.dependency_overrides[get_semantic_search_port]`. |
| OPS | Adopted | Se ChromaDB indisponivel a porta resolve para `None` (mesma falha graciosa de `get_report_indexer`); endpoints retornam 503 em vez de 500. Singleton de cliente reaproveitado (modelo carregado uma vez). |
| DATA | Adopted | Hidratacao por id pode encontrar ids no vectorstore ausentes no SQLite (relato deletado); use case pula ids sem `Report` correspondente em vez de quebrar. |

Review depth: auto=light (wiring contido, porta ja implementada), floor=light, flag=none -> effective=light. Sem override.

---

## Steps

### Step 1: Schema de resultado de busca com score

Editar `src/fala_gavea/presentation/schemas/report.py`:

Adicionar `ReportSearchResult` estendendo `ReportResponse` com o campo `score: float`. Reusa todos
os campos de `ReportResponse` (relato hidratado) e acrescenta o score de similaridade [0,1]
retornado pela porta.

```python
class ReportSearchResult(ReportResponse):
    score: float
```

- **Files**: `src/fala_gavea/presentation/schemas/report.py` (modify)
- **References**: `product-design/project/conventions.md` (schemas Pydantic em presentation/schemas)
- **Interface**: `ReportSearchResult(ReportResponse)` + `score: float`
- **Verify**: `uv run python -c "from fala_gavea.presentation.schemas.report import ReportSearchResult"`
- **Tests**: Coberto pelos Steps 6-7
- [x] Done

### Step 2: Use case SearchReports

Criar `src/fala_gavea/application/use_cases/reports/search_reports.py`:

```python
from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


class SearchReports:
    def __init__(self, report_repo: IReportRepository, search_port: ISemanticSearchPort) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(self, query: str, n: int = 10) -> list[tuple[Report, float]]:
        hits = self._search_port.search(query, n)
        results: list[tuple[Report, float]] = []
        for report_id, score in hits:
            report = self._report_repo.find_by_id(report_id)
            if report is not None:  # vectorstore pode ter id sem Report no SQLite
                results.append((report, score))
        return results
```

- **Files**: `src/fala_gavea/application/use_cases/reports/search_reports.py` (create)
- **References**: `src/fala_gavea/application/use_cases/reports/get_report.py` (padrao de use case), CONVENTION_1
- **Interface**: `SearchReports(report_repo, search_port).execute(query: str, n: int = 10) -> list[tuple[Report, float]]`
- **Depends on**: --
- **Verify**: `uv run pytest tests/unit/application/test_search_reports.py -v` (Step 6)
- **Tests**: Step 6
- [x] Done

### Step 3: Use case FindSimilarReports

Criar `src/fala_gavea/application/use_cases/reports/find_similar_reports.py`:

Valida que o relato base existe (`find_by_id`; senao `ReportNotFoundError` -> 404 no router),
chama `search_port.similar(report_id, n)`, hidrata os vizinhos por id (pulando ids ausentes no
SQLite). A porta ja exclui o proprio relato do resultado.

```python
from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.exceptions import ReportNotFoundError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ISemanticSearchPort


class FindSimilarReports:
    def __init__(self, report_repo: IReportRepository, search_port: ISemanticSearchPort) -> None:
        self._report_repo = report_repo
        self._search_port = search_port

    def execute(self, report_id: str, n: int = 5) -> list[tuple[Report, float]]:
        if self._report_repo.find_by_id(report_id) is None:
            raise ReportNotFoundError(f"Report not found: {report_id}")
        hits = self._search_port.similar(report_id, n)
        results: list[tuple[Report, float]] = []
        for rid, score in hits:
            report = self._report_repo.find_by_id(rid)
            if report is not None:
                results.append((report, score))
        return results
```

- **Files**: `src/fala_gavea/application/use_cases/reports/find_similar_reports.py` (create)
- **References**: `src/fala_gavea/application/use_cases/reports/get_report.py`, `domain/exceptions.py` (ReportNotFoundError)
- **Interface**: `FindSimilarReports(report_repo, search_port).execute(report_id: str, n: int = 5) -> list[tuple[Report, float]]`
- **Depends on**: --
- **Verify**: `uv run pytest tests/unit/application/test_find_similar_reports.py -v` (Step 7)
- **Tests**: Step 7
- [x] Done

### Step 4: Dependency get_semantic_search_port

Editar `src/fala_gavea/presentation/api/dependencies.py`:

Adicionar `get_semantic_search_port()` que retorna o **mesmo** singleton `ChromaSearchClient` ja
gerenciado por `get_report_indexer()` (a classe implementa `IReportIndexer` **e**
`ISemanticSearchPort`), evitando carregar o modelo de embedding duas vezes. Retorna
`ISemanticSearchPort | None`; `None` quando o ChromaDB esta indisponivel (mesma falha graciosa
existente).

```python
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer, ISemanticSearchPort

def get_semantic_search_port() -> ISemanticSearchPort | None:
    # ChromaSearchClient implementa IReportIndexer e ISemanticSearchPort;
    # reaproveita o singleton de get_report_indexer (modelo carregado uma vez).
    client = get_report_indexer()
    return client  # type: ignore[return-value]
```

- **Files**: `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **References**: `dependencies.py:93-102` (get_report_indexer, padrao de singleton lazy), `infrastructure/chromadb/chroma_search_client.py:13` (implementa ambas as portas)
- **Interface**: `get_semantic_search_port() -> ISemanticSearchPort | None`
- **Depends on**: --
- **Verify**: `uv run python -c "from fala_gavea.presentation.api.dependencies import get_semantic_search_port"`
- **Tests**: Coberto pelo Step 8 (override do dependency)
- [x] Done

### Step 5: Endpoints GET /reports/search e GET /reports/{id}/similar

Editar `src/fala_gavea/presentation/api/routers/reports.py`:

1. Imports: `SearchReports`, `FindSimilarReports`, `ISemanticSearchPort`, `get_semantic_search_port`, `ReportSearchResult`.
2. Adicionar helper interno para montar `ReportSearchResult` a partir de `(Report, score)` (mesma
   projecao usada em `create_report`/`get_report`, mais o `score`). Ou usar
   `ReportSearchResult(**ReportResponse.model_validate(report, from_attributes=...).model_dump(), score=score)`
   -- na pratica, montar explicitamente os campos para consistencia com os outros endpoints.
3. **Registrar `GET /reports/search` ANTES de `GET /{id}`** (linha 86) -- caso contrario FastAPI
   casa `/search` com a rota `/{id}`. Colocar logo apos `/geojson`.

```python
@router.get("/search", response_model=list[ReportSearchResult])
def search_reports(
    q: str,
    n: int = 10,
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> list[ReportSearchResult]:
    if not q.strip():
        raise HTTPException(status_code=422, detail="q must not be empty")
    if search_port is None:
        raise HTTPException(status_code=503, detail="Semantic search unavailable")
    n = max(1, min(n, 50))
    results = SearchReports(report_repo, search_port).execute(q, n)
    return [_to_search_result(r, score) for r, score in results]


@router.get("/{id}/similar", response_model=list[ReportSearchResult])
def similar_reports(
    id: str,
    n: int = 5,
    report_repo=Depends(get_report_repo),
    search_port: ISemanticSearchPort | None = Depends(get_semantic_search_port),
) -> list[ReportSearchResult]:
    if search_port is None:
        raise HTTPException(status_code=503, detail="Semantic search unavailable")
    n = max(1, min(n, 50))
    try:
        results = FindSimilarReports(report_repo, search_port).execute(id, n)
    except ReportNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [_to_search_result(r, score) for r, score in results]
```

`_to_search_result(report, score)` monta `ReportSearchResult` com os campos de `report`
(`urgency.value`, `status.value`, etc., como nos endpoints existentes) + `score`.

Ambos endpoints **publicos** (sem `get_current_user`), alinhado a `/geojson` e ao roadmap
("busca semantica e similares publicos").

- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- **References**: `routers/reports.py:58-83` (geojson publico, ordem antes de /{id}), `routers/reports.py:86-107` (get_report, projecao ReportResponse + 404)
- **Depends on**: Steps 1, 2, 3, 4
- **Verify**: `uv run uvicorn fala_gavea.presentation.api.main:app` sobe; `GET /reports/search?q=teste` nao colide com `/{id}`; `GET /docs` lista os dois endpoints
- **Tests**: Step 8
- [x] Done

### Step 6: Testes unitarios de SearchReports

Criar `tests/unit/application/test_search_reports.py`:

- `test_search_hydrates_and_keeps_score`: fake `ISemanticSearchPort.search` retorna
  `[("r1", 0.9), ("r2", 0.7)]`; repo mock retorna `Report` para cada id; verifica que o resultado
  preserva ordem e score e que `Report` foi hidratado.
- `test_search_skips_missing_ids`: porta retorna `[("r1", 0.9), ("ghost", 0.5)]`; repo retorna
  `None` para `"ghost"`; resultado contem apenas `r1`.
- `test_search_passes_n`: verifica que `n` e repassado para `search_port.search`.

Usar MagicMock para a porta e o repo; `Report` valido via `Report.create(...)` ou stub.

- **Files**: `tests/unit/application/test_search_reports.py` (create)
- **References**: `tests/unit/application/test_create_report_indexer.py` (padrao de mock de portas/repos)
- **Depends on**: Step 2
- **Verify**: `uv run pytest tests/unit/application/test_search_reports.py -v`
- **Tests**: N/A (este step e o teste)
- [x] Done

### Step 7: Testes unitarios de FindSimilarReports

Criar `tests/unit/application/test_find_similar_reports.py`:

- `test_similar_returns_neighbors`: repo `find_by_id(base)` retorna `Report`; porta
  `similar(base, n)` retorna `[("r2", 0.8)]`; repo retorna `Report` para `r2`; resultado contem `r2`.
- `test_similar_base_not_found_raises`: repo `find_by_id(base)` retorna `None`; `execute(base)`
  levanta `ReportNotFoundError`; verifica que `search_port.similar` **nao** foi chamado.
- `test_similar_skips_missing_neighbor_ids`: porta retorna id sem `Report` no repo -> pulado.

- **Files**: `tests/unit/application/test_find_similar_reports.py` (create)
- **References**: `tests/unit/application/test_create_report_indexer.py`, `domain/exceptions.py`
- **Depends on**: Step 3
- **Verify**: `uv run pytest tests/unit/application/test_find_similar_reports.py -v`
- **Tests**: N/A (este step e o teste)
- [x] Done

### Step 8: Testes de integracao dos endpoints (override da porta)

Criar `tests/test_reports_semantic.py`:

Usa as fixtures de `conftest.py` (`client`, `db_session`, `citizen_headers`, `sample_report_type`).
Define uma fake `ISemanticSearchPort` (classe simples retornando tuplas fixas) e a injeta via
`client.app.dependency_overrides[get_semantic_search_port] = lambda: fake`. Cria relatos reais via
`POST /reports` para que a hidratacao por id encontre `Report` no SQLite.

- `test_search_returns_results_with_score`: cria 1 relato; fake.search retorna `[(report_id, 0.9)]`;
  `GET /reports/search?q=buraco` -> 200, lista com 1 item contendo campos do relato + `score == 0.9`.
- `test_search_empty_q_returns_422`: `GET /reports/search?q=` -> 422.
- `test_search_missing_q_returns_422`: `GET /reports/search` (sem `q`) -> 422 (param obrigatorio).
- `test_search_unavailable_returns_503`: override retorna `None` -> `GET /reports/search?q=x` -> 503.
- `test_search_is_public`: sem header de auth -> 200 (endpoint publico).
- `test_similar_returns_neighbors`: cria 2 relatos (base + outro); fake.similar retorna
  `[(other_id, 0.8)]`; `GET /reports/{base}/similar` -> 200, item contem `other_id`, exclui base.
- `test_similar_base_not_found_404`: `GET /reports/{uuid-inexistente}/similar` -> 404.
- `test_similar_unavailable_returns_503`: override `None` -> 503.

Limpar `dependency_overrides` ao final de cada teste (ou usar fixture local) para nao vazar entre
testes -- a fixture `client` ja faz `clear()` no teardown.

- **Files**: `tests/test_reports_semantic.py` (create)
- **References**: `tests/conftest.py` (fixtures, padrao de `dependency_overrides`), `tests/test_reports.py` (padrao de TestClient + geojson)
- **Depends on**: Steps 1-5
- **Verify**: `uv run pytest tests/test_reports_semantic.py -v`
- **Tests**: N/A (este step e o teste)
- [x] Done

### Step 9: Suite completa + lint + type check

- **Files**: -- (verificacao)
- **Depends on**: Steps 1-8
- **Verify**: `uv run pytest` (toda a suite verde, sem regressao), `uv run ruff check src/ tests/`, `uv run pyright src/`
- **Tests**: N/A
- [x] Done

---

## Post-plan: atualizar roadmap

Apos `/implement`, marcar no `roadmap-00002-wave2-espacos-semanticos-ia.md` os itens 3 e 4 (Wave 1)
como `done` e preencher a coluna `Plan` com `plan-000094` (substitui `plan-TBD`).

---

## Commit Message

```
feat(semantic): GET /reports/search + GET /reports/{id}/similar (wave 1)

Wave 1 of roadmap-000088: semantic search endpoints over the existing
ISemanticSearchPort (ChromaSearchClient).
- SearchReports use case: semantic search, hydrates Reports by id, keeps score
- FindSimilarReports use case: semantic neighbors, 404 if base missing, self-excluded
- dependencies.py: get_semantic_search_port() reuses the ChromaSearchClient singleton
- reports router: public GET /reports/search (registered before /{id}) and
  GET /reports/{id}/similar; 503 when ChromaDB unavailable
- ReportSearchResult schema (ReportResponse + score)
- unit + integration tests with a fake ISemanticSearchPort (no model/ChromaDB load)

Plan: plan-000094
```

---

## Implementation Summary | 2026-06-19 15:02 UTC

**Mode:** in-context sequential (manual topology). All 9 steps completed (9/9 done), 0 partial/failed.

### Changes
- **`presentation/schemas/report.py`** — added `ReportSearchResult(ReportResponse)` with `score: float`.
- **`application/use_cases/reports/search_reports.py`** (new) — `SearchReports.execute(query, n)`; queries `ISemanticSearchPort.search`, hydrates each hit via `IReportRepository.find_by_id`, skips vectorstore ids absent in SQLite, preserves score/order.
- **`application/use_cases/reports/find_similar_reports.py`** (new) — `FindSimilarReports.execute(report_id, n)`; raises `ReportNotFoundError` if base missing (→404), calls `similar()` (port self-excludes base), hydrates neighbors, skips missing ids.
- **`presentation/api/dependencies.py`** — added `get_semantic_search_port() -> ISemanticSearchPort | None`, reusing the `get_report_indexer()` `ChromaSearchClient` singleton (model loaded once); returns `None` when ChromaDB unavailable.
- **`presentation/api/routers/reports.py`** — `_to_search_result(report, score)` helper; public `GET /reports/search` (registered BEFORE `/{id}` to avoid path collision) and public `GET /reports/{id}/similar`; both return 503 when port is `None`, `/search` returns 422 on empty `q`, `/similar` returns 404 on missing base; `n` clamped to [1,50].
- **Tests** — `tests/unit/application/test_search_reports.py` (3), `tests/unit/application/test_find_similar_reports.py` (3), `tests/test_reports_semantic.py` (8 integration via fake `ISemanticSearchPort` override). Also removed 2 pre-existing unused imports flagged by ruff (`test_create_report_indexer.py`, `test_embedding_registry.py`).

### Quality Gate
- **pytest:** 67 passed (14 new). **ruff:** clean. **pyright:** no new errors in changed files (49 pre-existing SQLAlchemy `Column`-typing / geojson-bbox baseline errors untouched).
- **standards-checker (validate):** 6/20; all 14 failures are pre-existing harness/template path mismatches (scripts assume a `backend/app/` Flask layout) or harness-internal state — none implicate plan-000094 files.
- **code-reviewer (deep):** no HIGH/blocking. ARCH/API/TEST Adopted (CONVENTION_1/2/3 + S3 satisfied). Findings recorded as deferred below.

### Deferred items (advisory — not blocking)
- **[MEDIUM SEC/PERF]** No rate limiting on the public, embedding-compute-heavy `/search` + `/{id}/similar` endpoints. Relevant before any public (non-localhost) deploy — see research-000091.
- **[MEDIUM DATA/SEC]** Public projection exposes full report `text` + `author_id` + precise coords to anonymous callers. Confirm privacy posture or add a redacted public schema. (Stems from the intentional public design per roadmap-000088 / `/geojson` precedent.)
- **[LOW PERF]** N+1 hydration (`find_by_id` per hit) — consider a batch `find_by_ids` when result sizes grow.
- **[LOW API]** `n` silently clamped via `max/min` (implemented to plan spec); could use `Query(ge=1, le=50)` for OpenAPI-documented 422.
- **[LOW TEST]** Base-report self-exclusion verified only at the Chroma layer, not defended in the use case.

### Roadmap
roadmap-00002 (roadmap-000088) Wave 1 items 3 (semantic-search) and 4 (similar-reports) flipped to `done`, Plan column set to `plan-000094`.
