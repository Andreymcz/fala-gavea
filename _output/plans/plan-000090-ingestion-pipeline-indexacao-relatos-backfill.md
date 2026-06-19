# Plan 000090 | FEATURE -B | 2026-06-19 12:34 | ingestion pipeline indexacao relatos backfill | Review: light
plan_format_version: 1

source: roadmap-000088 -- Wave 0 item 2 (ingestion-pipeline: hook em CreateReport + backfill)

## Brief (verbatim)
roadmap 2 wave 0

## Agent Interpretation

Implementar o pipeline de ingestao semantica (Wave 0, item 2 do roadmap-000088):
- Injetar `IReportIndexer` em `CreateReport` via porta de dominio; chamar `index(report)` apos `save()`
- Tolerancia a falha: erro de indexacao loga warning mas nao derruba a criacao do relato
- Atualizar `dependencies.py` com `get_report_indexer()` que retorna `ChromaSearchClient`
- Atualizar router de reports para injetar o indexer
- Script `scripts/backfill_semantic.py` idempotente para indexar os ~10k relatos existentes

Depende do plan-000089 (ChromaSearchClient e portas de dominio devem estar implementados).

## Files

- `src/fala_gavea/application/use_cases/reports/create_report.py` (modify)
- `src/fala_gavea/presentation/api/dependencies.py` (modify)
- `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- `scripts/backfill_semantic.py` (create)
- `tests/unit/application/test_create_report_indexer.py` (create)

## Review

### Perspectives Evaluated

| Tag | Verdict | Notes |
|-----|---------|-------|
| ARCH | Adopted | `CreateReport` recebe `IReportIndexer` (porta de dominio) -- sem import de chromadb no use case. Dependencia vai de application -> domain (OK). |
| TEST | Adopted | `IReportIndexer` e mockavel via MagicMock; testes cobrem caminho feliz + falha de index. |
| OPS | Adopted | Backfill idempotente: verifica ids ja indexados antes de adicionar. Script roda fora do servidor. |

---

## Steps

### Step 1: Modificar CreateReport para aceitar IReportIndexer opcional

Editar `src/fala_gavea/application/use_cases/reports/create_report.py`:

Adicionar `indexer: IReportIndexer | None = None` ao `__init__`. Apos `self._report_repo.save(...)` retornar o relato, se `self._indexer` for nao-None, chamar `self._indexer.index(report)` dentro de um bloco `try/except Exception` que loga o erro como WARNING e segue (nao re-lanca).

```python
import logging
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer

_log = logging.getLogger(__name__)

class CreateReport:
    def __init__(
        self,
        report_repo: IReportRepository,
        report_type_repo: IReportTypeRepository,
        indexer: IReportIndexer | None = None,
    ) -> None:
        ...
        self._indexer = indexer

    def execute(self, ...) -> Report:
        ...
        report = self._report_repo.save(Report.create(...))
        if self._indexer is not None:
            try:
                self._indexer.index(report)
            except Exception as exc:
                _log.warning("Failed to index report %s: %s", report.id, exc)
        return report
```

O indexer e opcional (default None) para garantir retrocompatibilidade com testes existentes que nao passam indexer.

- **Files**: `src/fala_gavea/application/use_cases/reports/create_report.py` (modify)
- **References**: `product-design/project/standards.md § Backend § 2. Layer Boundaries`
- **Interface**: `CreateReport.__init__(report_repo, report_type_repo, indexer=None)` -- assinatura existente mantida compativel (indexer e kwargs)
- **Verify**: `uv run pytest tests/test_reports.py -v` passa (testes existentes nao quebram pois indexer default None)
- **Tests**: Coberto pelo Step 3
- [ ] Done

### Step 2: Adicionar get_report_indexer a dependencies.py e atualizar router

Editar `src/fala_gavea/presentation/api/dependencies.py`:

Adicionar `get_report_indexer()` como FastAPI dependency. Ele instancia `ChromaSearchClient(SemanticConfig())` e o retorna como `IReportIndexer`. Se a instanciacao falhar (e.g., chromadb nao disponivel), loga warning e retorna None -- assim o servidor sobe mesmo sem o vectorstore pronto.

```python
from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer

_indexer_instance: IReportIndexer | None = None

def get_report_indexer() -> IReportIndexer | None:
    global _indexer_instance
    if _indexer_instance is None:
        try:
            _indexer_instance = ChromaSearchClient(SemanticConfig())
        except Exception as exc:
            _log.warning("ChromaSearchClient unavailable: %s", exc)
    return _indexer_instance
```

Nota: singleton em modulo e adequado para o PoC. O modelo de embedding e carregado uma vez por processo.

Editar `src/fala_gavea/presentation/api/routers/reports.py`:

No endpoint `create_report`, adicionar `indexer: IReportIndexer | None = Depends(get_report_indexer)` como parametro e passar para `CreateReport(report_repo, report_type_repo, indexer=indexer)`.

Adicionar o import de `get_report_indexer` no router.

- **Files**: `src/fala_gavea/presentation/api/dependencies.py` (modify), `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- **References**: `product-design/project/constitution.md T1`, `product-design/project/constitution.md T2`
- **Depends on**: Step 1 (plan-000090), plan-000089 (ChromaSearchClient deve existir)
- **Verify**: `uv run uvicorn fala_gavea.presentation.api.main:app --reload` sobe sem erro (mesmo sem vectorstore); POST /reports ainda retorna 201
- **Tests**: Coberto pelos testes de integracao existentes em `tests/test_reports.py` (indexer nao e injetado no TestClient -- app.dependency_overrides pode sobrescrever para None ou mock)
- [ ] Done

### Step 3: Testes unitarios do hook de indexacao em CreateReport

Criar `tests/unit/application/test_create_report_indexer.py`:

- `test_indexer_called_after_save`: criar MagicMock para IReportIndexer; criar stubs de IReportRepository e IReportTypeRepository; chamar `CreateReport(repo, rt_repo, indexer=mock_indexer).execute(...)`; verificar `mock_indexer.index.assert_called_once()` com o relato retornado pelo repo
- `test_indexer_failure_does_not_raise`: configurar `mock_indexer.index.side_effect = Exception("chroma down")`; chamar `execute(...)` e verificar que retorna `Report` sem lancar excecao
- `test_no_indexer_skips_index`: passar `indexer=None`; verificar que nenhum AttributeError ou erro e lancado (caminho legado sem indexer)

Os stubs de repo podem ser MagicMock configurados para retornar um `Report` e um `ReportType` validos respectivamente.

- **Files**: `tests/unit/application/test_create_report_indexer.py` (create)
- **Depends on**: Step 1
- **Verify**: `uv run pytest tests/unit/application/test_create_report_indexer.py -v` passa
- **Tests**: N/A (este step eh o teste)
- [ ] Done

### Step 4: Script de backfill idempotente

Criar `scripts/backfill_semantic.py`:

Script standalone que:
1. Le todos os Reports do banco SQLite via SQLAlchemy (reutiliza `SessionLocal` e `SQLAlchemyReportRepository`)
2. Instancia `ChromaSearchClient(SemanticConfig())`
3. Para cada relato, verifica se o `report.id` ja esta indexado (`collection.get(ids=[report.id])` retorna vazio?); se nao, chama `indexer.index(report)`
4. Imprime progresso a cada 500 relatos
5. Ao final, imprime total indexado vs. total pulado (ja existia)

Usage:
```
uv run python scripts/backfill_semantic.py
```

Argumentos opcionais: `--batch-size N` (default 100, quantos encode por vez via SentenceTransformer); `--force` (re-indexa mesmo os ja indexados, util para mudar o modelo).

Nota: o script roda fora do servidor FastAPI, diretamente contra o SQLite e o vectorstore. Nao usa a API HTTP.

- **Files**: `scripts/backfill_semantic.py` (create)
- **Depends on**: Step 2 (plan-000090) -- ChromaSearchClient e SemanticConfig ja existem
- **Verify**: `uv run python scripts/backfill_semantic.py --help` mostra ajuda; rodando com banco vazio completa sem erro; rodando duas vezes nao duplica entradas (idempotente)
- **Tests**: N/A (script operacional; testar backfill real requereria banco populado -- adequado para teste manual)
- [ ] Done

---

## Commit Message

```
feat(semantic): Inject IReportIndexer into CreateReport; backfill script

Wave 0 item 2 of roadmap-000088: ingestion pipeline for semantic spaces.
- CreateReport accepts optional IReportIndexer; index() called after save()
- Index failures log a warning and do not abort report creation
- dependencies.py: get_report_indexer() provides ChromaSearchClient singleton
- reports router passes indexer to CreateReport
- scripts/backfill_semantic.py indexes existing ~10k reports (idempotent)

Plan: plan-000090
```
