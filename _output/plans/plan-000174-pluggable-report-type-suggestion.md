# Plan 000174 | FEATURE-X | 2026-06-25 21:35 | Pluggable report-type suggestion: sentinel + ChromaDB + DistilBERT | Review: standard
plan_format_version: 1
source: research-000172 -- design space for AI-assisted report_type suggestion with pluggable backends

## Brief

source:research 172 vamos planejar a implementacao da feature de sugestao de reporttype. vamos arquiteturar de forma que seja simples trocar as 2 abordagens chromadb e distilbert. o fine-tunning sera feito offline

## Agent Interpretation

Implement AI-assisted `report_type` suggestion for reports submitted without a type. The architecture uses a single `IReportTypeSuggestionPort` port with two interchangeable implementations -- `ChromaReportTypeSuggestionClient` (semantic similarity on ReportType name/description embeddings) and `DistilBERTSuggestionClient` (loads fine-tuned classifier from disk, inference-only). Active backend is selected by `FALA_GAVEA_SUGGESTION_BACKEND` env var (default: `chromadb`). Fine-tuning is done offline; this plan covers only the inference integration.

Supporting changes per research-000172:
- Sentinel `ReportType` id=`"unknown"` for reports submitted without a type
- `report_type_source` provenance enum on `Report`
- Bug fix: `save()` silently discards `report_type_id` updates
- `PATCH /reports/{id}/report-type` for agent/admin confirmation
- `awaiting_type_review` filter for the review queue

## Files

### Modified
- `src/fala_gavea/domain/entities/report.py` -- add `ReportTypeSource` enum + `report_type_source` field
- `src/fala_gavea/domain/repositories/semantic_ports.py` -- add `IReportTypeSuggestionPort` + `SuggestionResult`
- `src/fala_gavea/infrastructure/database/models.py` -- add `report_type_source` column to `ReportModel`
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` -- fix `save()` bug
- `src/fala_gavea/infrastructure/embeddings/registry.py` -- add `topic_model_dir` to `SemanticConfig`
- `src/fala_gavea/presentation/api/dependencies.py` -- add `get_report_type_suggester()` singleton
- `src/fala_gavea/application/use_cases/reports/create_report.py` -- accept optional `report_type_id`, call suggester
- `src/fala_gavea/presentation/schemas/report.py` -- optional `report_type_id`, add schemas, `report_type_source` in response
- `src/fala_gavea/presentation/api/routers/reports.py` -- add PATCH endpoint, modify POST, add filter
- `src/fala_gavea/domain/repositories/report_repository.py` -- add `awaiting_type_review` to `ReportFilters`
- `scripts/seed_report_types.py` -- add sentinel `ReportType`
- `frontend/src/components/ReportTable.tsx` (or equivalent row component) -- `ai_suggested` badge
- `frontend/src/components/FilterPanel.tsx` (or equivalent) -- `awaiting_type_review` toggle

### Created
- `src/fala_gavea/infrastructure/chromadb/chroma_report_type_client.py` -- ChromaDB suggestion client
- `src/fala_gavea/infrastructure/topics/distilbert_suggestion_client.py` -- DistilBERT suggestion client
- `src/fala_gavea/application/use_cases/reports/suggest_report_type.py` -- thin use case wrapper
- `src/fala_gavea/application/use_cases/reports/update_report_type.py` -- PATCH use case

---

## Steps

### Step 1: Domain model -- ReportTypeSource enum, SuggestionResult, IReportTypeSuggestionPort

Add `ReportTypeSource` as a `str` enum to `report.py` with values `citizen`, `ai_suggested`, `agent_override`. Add `report_type_source: ReportTypeSource | None = None` field to the `Report` dataclass (nullable so legacy records without provenance remain valid). Update `Report.create()` to accept an optional `report_type_source` parameter (defaults to `None`; callers that omit it stay unchanged).

In `semantic_ports.py`, add:
```python
from dataclasses import dataclass

@dataclass
class SuggestionResult:
    report_type_id: str
    report_type_name: str
    confidence: float  # [0, 1]

class IReportTypeSuggestionPort(ABC):
    @abstractmethod
    def suggest(self, text: str, n: int = 3) -> list[SuggestionResult]:
        """Return up to n ranked suggestions. Returns [] when not ready."""
        ...

    @abstractmethod
    def ready(self) -> bool:
        """True if the backend is initialized and can serve suggestions."""
        ...
```

- **Files**: `src/fala_gavea/domain/entities/report.py` (modify), `src/fala_gavea/domain/repositories/semantic_ports.py` (modify)
- **References**: `product-design/conventions.md`
- **Interface**: exports `ReportTypeSource` enum, `SuggestionResult` dataclass, `IReportTypeSuggestionPort` ABC; `Report.report_type_source: ReportTypeSource | None`
- **Verify**: `uv run python -c "from fala_gavea.domain.entities.report import ReportTypeSource; from fala_gavea.domain.repositories.semantic_ports import IReportTypeSuggestionPort, SuggestionResult; print('ok')"` exits 0
- **Tests**: Add unit tests verifying `ReportTypeSource` values, `SuggestionResult` field types, and that `IReportTypeSuggestionPort` cannot be instantiated directly
- [ ] Done

### Step 2: DB model, seed sentinel, fix save() bug

**DB model**: Add `report_type_source` column to `ReportModel`:
```python
report_type_source = Column(
    SAEnum("citizen", "ai_suggested", "agent_override", name="report_type_source"),
    nullable=True,  # NULL = legacy records
)
```
`Base.metadata.create_all()` adds the column on fresh DBs. For existing DBs provide a manual migration comment in the file.

**Fix `save()` bug** in `SQLAlchemyReportRepository`: in the update branch (when `model is not None`), add:
```python
model.report_type_id = report.report_type_id
model.report_type_source = report.report_type_source.value if report.report_type_source else None
```

**Update `_to_model()` and `_to_entity()`** to map `report_type_source` bidirectionally.

**Sentinel seed**: add to `scripts/seed_report_types.py` (or create if absent) a seed entry:
```python
{"id": "unknown", "name": "Nao classificado", "description": "Tipo nao informado pelo cidadao", "active": True}
```
Ensure it is idempotent (insert-or-ignore). The sentinel must be seeded before any other seed that creates reports without a type.

**Update `ReportFilters`** in `src/fala_gavea/domain/repositories/report_repository.py`: add `awaiting_type_review: bool = False`. In `SQLAlchemyReportRepository.find_all()` and `find_page()`: when `awaiting_type_review=True`, filter `report_type_source == "ai_suggested" OR report_type_id == "unknown"`.

- **Files**: `src/fala_gavea/infrastructure/database/models.py` (modify), `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` (modify), `src/fala_gavea/domain/repositories/report_repository.py` (modify), `scripts/seed_report_types.py` (modify or create)
- **Depends on**: Step 1
- **Interface**: `SQLAlchemyReportRepository.save()` now persists `report_type_id` and `report_type_source`; `ReportFilters.awaiting_type_review: bool`
- **Verify**: `uv run pytest tests/ -k "report_repository or report_type"` passes; `save()` with updated `report_type_id` round-trips correctly
- **Tests**: Add test: create a report, update its `report_type_id` via `save()`, verify the DB row reflects the new value. Add test for `awaiting_type_review` filter returning only AI-suggested or unknown-type reports.
- [ ] Done

### Step 3: ChromaDB suggestion client

Create `src/fala_gavea/infrastructure/chromadb/chroma_report_type_client.py`:

```python
class ChromaReportTypeSuggestionClient(IReportTypeSuggestionPort):
    """Suggests ReportType by embedding-similarity on ReportType name+description.

    Uses a separate ChromaDB collection 'falagavea_report_types' -- independent
    from the reports search collection. Indexed at construction time from the
    report_type_repository.
    """
    _COLLECTION = "falagavea_report_types"

    def __init__(self, config: SemanticConfig, report_types: list[ReportType]) -> None:
        # init chroma client, sentence transformer (same model as ChromaSearchClient)
        # index all active ReportTypes by name + description
        ...

    def suggest(self, text: str, n: int = 3) -> list[SuggestionResult]:
        # encode text as query, query collection, convert distance to confidence
        # filter out sentinel id="unknown" from results
        ...

    def ready(self) -> bool:
        return True
```

The `report_types` list is fetched once at construction time from `IReportTypeRepository.find_all()` (excluding the sentinel). The singleton in `dependencies.py` (Step 5) passes this list.

Encoding: `query: <text>` for user reports; `passage: <name>. <description>` for ReportTypes (same multilingual-e5 convention as `ChromaSearchClient`).

Confidence mapping: `1.0 / (1.0 + distance)` -- same formula as `ChromaSearchClient.search()`.

- **Files**: `src/fala_gavea/infrastructure/chromadb/chroma_report_type_client.py` (create)
- **Depends on**: Step 1
- **Interface**: `ChromaReportTypeSuggestionClient(config: SemanticConfig, report_types: list[ReportType])` implements `IReportTypeSuggestionPort`
- **Verify**: `uv run pytest tests/ -k "chroma_report_type"` passes
- **Tests**: Unit test with 3 mock ReportTypes indexed; call `suggest("Calcada quebrada")`, assert result contains expected report_type_id with confidence > 0; test `ready()` returns True.
- [ ] Done

### Step 4: DistilBERT suggestion client

Create `src/fala_gavea/infrastructure/topics/distilbert_suggestion_client.py`:

```python
class DistilBERTSuggestionClient(IReportTypeSuggestionPort):
    """Wraps the offline fine-tuned DistilBERT model for ReportType classification.

    'Fine-tuning' = gradient-descent weight updates on distilbert-base-multilingual-cased
    using labeled relatos corpus (HuggingFace Trainer API). Model loaded from disk at init.
    Inference-only; re-training is done offline via the Jupyter notebook.
    """

    def __init__(self, config: SemanticConfig, report_types: list[ReportType]) -> None:
        # Load tokenizer + model from config.topic_model_dir / "best"
        # Load label_map.json (int -> label string)
        # Build label_to_report_type mapping: normalize label names, match against report_types
        # self._ready = True on success; False if model dir absent
        ...

    def suggest(self, text: str, n: int = 3) -> list[SuggestionResult]:
        # tokenize text, run forward pass, softmax, return top-n as SuggestionResult
        # confidence = softmax probability
        # filter labels that have no mapping in label_to_report_type
        ...

    def ready(self) -> bool:
        return self._ready
```

Add `topic_model_dir: str` to `SemanticConfig` (default: `os.getenv("FALA_GAVEA_TOPIC_MODEL_DIR", "./models/topic_classifier")`).

Label-to-report_type mapping:
1. Normalize both sides: lowercase + remove accents + strip spaces
2. Match automatically; unmapped labels are excluded from results
3. If `models/topic_classifier/label_to_report_type.json` exists, use it as override (admin-editable)

Graceful degradation: if `models/topic_classifier/best/` does not exist, `ready()` returns False and `suggest()` returns `[]`. No exception propagates to callers.

Dependencies to add to `pyproject.toml`: `"transformers>=4.40"`, `"torch>=2.0"` (CPU-only inference is sufficient).

- **Files**: `src/fala_gavea/infrastructure/topics/distilbert_suggestion_client.py` (create), `src/fala_gavea/infrastructure/embeddings/registry.py` (modify), `pyproject.toml` (modify)
- **Depends on**: Step 1
- **Interface**: `DistilBERTSuggestionClient(config: SemanticConfig, report_types: list[ReportType])` implements `IReportTypeSuggestionPort`; `SemanticConfig.topic_model_dir: str`
- **Verify**: `uv run python -c "from fala_gavea.infrastructure.topics.distilbert_suggestion_client import DistilBERTSuggestionClient; print('import ok')"` exits 0 (model absence handled gracefully)
- **Tests**: Unit test with model dir absent: `ready()` returns False, `suggest(...)` returns []. If fixture model is available: assert top-1 result has a non-empty `report_type_id`.
- [ ] Done

### Step 5: Dependency wiring -- get_report_type_suggester() singleton

Add to `dependencies.py`:

```python
_SUGGESTION_INIT_FAILED = object()
_suggester_instance: IReportTypeSuggestionPort | None | object = None
_suggester_lock = threading.Lock()

def get_report_type_suggester() -> IReportTypeSuggestionPort | None:
    global _suggester_instance
    if _suggester_instance is _SUGGESTION_INIT_FAILED:
        return None
    if _suggester_instance is not None:
        return _suggester_instance  # type: ignore[return-value]
    with _suggester_lock:
        if _suggester_instance is not None:
            return None if _suggester_instance is _SUGGESTION_INIT_FAILED else _suggester_instance
        try:
            from fala_gavea.infrastructure.embeddings.registry import SemanticConfig
            from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository
            backend = os.getenv("FALA_GAVEA_SUGGESTION_BACKEND", "chromadb").lower()
            config = SemanticConfig()
            # Fetch report types for index seeding (ephemeral session)
            db = SessionLocal()
            try:
                rts = SQLAlchemyReportTypeRepository(db).find_all()
            finally:
                db.close()
            active_rts = [rt for rt in rts if rt.active and rt.id != "unknown"]
            if backend == "distilbert":
                from fala_gavea.infrastructure.topics.distilbert_suggestion_client import DistilBERTSuggestionClient
                _suggester_instance = DistilBERTSuggestionClient(config, active_rts)
            else:
                from fala_gavea.infrastructure.chromadb.chroma_report_type_client import ChromaReportTypeSuggestionClient
                _suggester_instance = ChromaReportTypeSuggestionClient(config, active_rts)
        except Exception as exc:
            _log.warning("ReportType suggester unavailable: %s", exc)
            _suggester_instance = _SUGGESTION_INIT_FAILED
    return None if _suggester_instance is _SUGGESTION_INIT_FAILED else _suggester_instance  # type: ignore[return-value]
```

Add `FALA_GAVEA_SUGGESTION_BACKEND` to the env var documentation in `CLAUDE.md` (alongside existing vars).

- **Files**: `src/fala_gavea/presentation/api/dependencies.py` (modify), `CLAUDE.md` (modify -- add env var)
- **Depends on**: Step 3, Step 4
- **Interface**: `get_report_type_suggester() -> IReportTypeSuggestionPort | None`
- **Verify**: `uv run uvicorn fala_gavea.presentation.api.main:app --reload` starts without error; log shows which backend initialized
- **Tests**: Covered by integration in Steps 7-8; unit-test the factory: mock both clients, verify correct one is selected per env var.
- [ ] Done

### Step 6: Use cases -- SuggestReportType, UpdateReportType, modify CreateReport

**Create `SuggestReportTypeUseCase`** in `src/fala_gavea/application/use_cases/reports/suggest_report_type.py`:

```python
class SuggestReportType:
    def __init__(self, suggester: IReportTypeSuggestionPort | None) -> None:
        self._suggester = suggester

    def execute(self, text: str, n: int = 3) -> list[SuggestionResult]:
        if self._suggester is None or not self._suggester.ready():
            return []
        return self._suggester.suggest(text, n=n)
```

**Create `UpdateReportTypeUseCase`** in `src/fala_gavea/application/use_cases/reports/update_report_type.py`:

```python
class UpdateReportType:
    def __init__(
        self,
        report_repo: IReportRepository,
        report_type_repo: IReportTypeRepository,
        indexer: IReportIndexer | None = None,
    ) -> None: ...

    def execute(self, report_id: str, report_type_id: str, source: ReportTypeSource) -> Report:
        report = self._report_repo.find_by_id(report_id)
        if report is None:
            raise ReportNotFoundError(report_id)
        rt = self._report_type_repo.find_by_id(report_type_id)
        if rt is None or not rt.active:
            raise ReportTypeNotFoundError(report_type_id)
        report.report_type_id = report_type_id
        report.report_type_source = source
        saved = self._report_repo.save(report)
        if self._indexer is not None:
            try:
                self._indexer.delete(report_id)
                self._indexer.index(saved)
            except Exception as exc:
                _log.warning("Failed to re-index report %s: %s", report_id, exc)
        return saved
```

**Modify `CreateReport.execute()`**: make `report_type_id` optional (`str | None = None`). When `None`, call `SuggestReportTypeUseCase.execute(text)` and use the top result's `report_type_id`; set `report_type_source = ReportTypeSource.ai_suggested`. If no suggestion available, fall back to sentinel `id="unknown"` with `report_type_source = None`. When `report_type_id` is provided by citizen, set `report_type_source = ReportTypeSource.citizen`.

- **Files**: `src/fala_gavea/application/use_cases/reports/suggest_report_type.py` (create), `src/fala_gavea/application/use_cases/reports/update_report_type.py` (create), `src/fala_gavea/application/use_cases/reports/create_report.py` (modify)
- **Depends on**: Step 1, Step 2, Step 5
- **Interface**: `SuggestReportType.execute(text, n) -> list[SuggestionResult]`; `UpdateReportType.execute(report_id, report_type_id, source) -> Report`
- **Verify**: `uv run pytest tests/ -k "suggest_report_type or update_report_type or create_report"` passes
- **Tests**: `SuggestReportType` -- test with `None` suggester returns []; test with mock suggester returns results. `UpdateReportType` -- test updates `report_type_id` and triggers re-index. `CreateReport` -- test with no `report_type_id` uses sentinel when suggester returns []; uses top suggestion when available.
- [ ] Done

### Step 7: Pydantic schemas

In `src/fala_gavea/presentation/schemas/report.py`:

1. Make `ReportCreate.report_type_id` optional: `report_type_id: str | None = None`
2. Add `report_type_source: str | None` to `ReportResponse` (nullable; `None` for legacy records)
3. Add `awaiting_type_review: bool = False` to `ReportQueryRequest`
4. Add new schemas:
   ```python
   class ReportTypePatchRequest(BaseModel):
       report_type_id: str

   class SuggestionItem(BaseModel):
       report_type_id: str
       report_type_name: str
       confidence: float

   class SuggestionResponse(BaseModel):
       suggestions: list[SuggestionItem]
       backend: str  # "chromadb" | "distilbert" | "unavailable"
   ```

- **Files**: `src/fala_gavea/presentation/schemas/report.py` (modify)
- **Depends on**: Step 1
- **Interface**: all schema classes above
- **Verify**: `uv run python -c "from fala_gavea.presentation.schemas.report import ReportTypePatchRequest, SuggestionResponse; print('ok')"` exits 0
- **Tests**: Covered by router tests in Step 8.
- [ ] Done

### Step 8: API routers -- PATCH endpoint, suggest endpoint, creation update, filter

In `src/fala_gavea/presentation/api/routers/reports.py`:

1. **`PATCH /reports/{id}/report-type`** -- role: agent or admin:
   ```
   @router.patch("/{report_id}/report-type", response_model=ReportResponse)
   def update_report_type(report_id: str, body: ReportTypePatchRequest, current_user=Depends(_agent_or_admin), ...):
       uc = UpdateReportType(report_repo, report_type_repo, indexer)
       report = uc.execute(report_id, body.report_type_id, ReportTypeSource.agent_override)
       return ReportResponse.model_validate(report)
   ```

2. **`GET /reports/{id}/suggest-type`** -- no auth required (public):
   ```
   @router.get("/{report_id}/suggest-type", response_model=SuggestionResponse)
   def suggest_report_type(report_id: str, suggester=Depends(get_report_type_suggester), report_repo=...):
       report = report_repo.find_by_id(report_id)
       if report is None: raise HTTPException(404)
       uc = SuggestReportType(suggester)
       results = uc.execute(report.text)
       backend = "unavailable" if suggester is None else ("distilbert" if ... else "chromadb")
       return SuggestionResponse(suggestions=[...], backend=backend)
   ```

3. **Modify `POST /reports`**: pass `report_type_id=body.report_type_id` (now optional `str | None`) and inject `suggester=Depends(get_report_type_suggester)` into `CreateReport`.

4. **`awaiting_type_review` filter**: in the `/reports/query` handler, pass `filters.awaiting_type_review` to `ReportFilters`.

- **Files**: `src/fala_gavea/presentation/api/routers/reports.py` (modify)
- **Depends on**: Step 6, Step 7
- **Interface**: `PATCH /reports/{id}/report-type` (200 ReportResponse | 403 | 404); `GET /reports/{id}/suggest-type` (200 SuggestionResponse | 404)
- **Verify**: `uv run pytest tests/ -k "report" -v` passes; manual: `PATCH /reports/{id}/report-type` with agent token updates report; `GET /reports/{id}/suggest-type` returns suggestions
- **Tests**: Test `PATCH` returns 403 for citizen; 404 for missing report; 200 with updated `report_type_id`. Test `GET suggest-type` returns `SuggestionResponse` with `backend` field.
- **Docs**: Update API reference (if maintained) with the two new endpoints and the updated `POST /reports` schema
- [ ] Done

### Step 9: Frontend -- ai_suggested badge + awaiting_type_review filter toggle

Two UI changes in the React SPA:

1. **`ai_suggested` badge** on report rows: when `report.report_type_source === "ai_suggested"`, render a small badge (e.g., `<Badge variant="outline">IA</Badge>` in Tailwind) next to the `report_type` column or the type chip in the map popup. Clicking the badge could link to the PATCH flow (future). For now, display-only.

2. **`awaiting_type_review` filter toggle** in the filter panel sidebar: add a boolean toggle/checkbox labeled "Relatos aguardando revisao de topico" (or "Sem topico"). When enabled, sets `awaiting_type_review: true` in the `ReportQueryRequest` payload.

Note: identify the exact component files by inspecting `frontend/src/` -- common candidates are `ReportTable.tsx`, `ReportRow.tsx`, `FilterPanel.tsx`, or `WorkspaceFilters.tsx`. Adjust file names in the step to match what exists.

- **Files**: relevant `frontend/src/` components (modify -- identify during implementation), `frontend/src/types/report.ts` or equivalent (add `report_type_source?: string`, `awaiting_type_review?:boolean` to types)
- **Depends on**: Step 7, Step 8
- **Interface**: N/A (UI only)
- **Verify**: `cd frontend && npm run build` exits 0; visual check: report row with `report_type_source === "ai_suggested"` shows the "IA" badge; enabling the filter returns only matching reports
- **Tests**: `cd frontend && npm run test` passes; add test for badge rendering when `report_type_source === "ai_suggested"`
- **Docs**: N/A
- [ ] Done

---

## Review

### Engineering perspectives

| Perspective | Status | Notes |
|---|---|---|
| P0 - Correctness | Adopted | Bug fix for `save()` explicitly planned in Step 2; sentinel avoids nullable constraint violation |
| P0 - Security | Adopted | PATCH endpoint gated behind `require_any_role("agent", "admin")`; suggest endpoint is read-only and safe to expose publicly |
| P1 - Architecture | Adopted | Port + two implementations; active backend via env var; no direct ChromaDB/torch imports in use cases |
| P1 - Data integrity | Adopted | Sentinel prevents NULL `report_type_id`; `report_type_source` is nullable for legacy compatibility |
| P2 - Performance | Adopted | Singleton pattern for both clients (model loaded once); suggestion is synchronous but lightweight for ChromaDB; DistilBERT CPU inference acceptable for current QPS |
| P2 - Testing | Adopted | Each step specifies unit tests; mock-based for use cases; integration for repo and routers |
| P3 - Observability | Adopted | Existing `_log.warning()` pattern in `dependencies.py` extended to new singleton |
| P3 - Frontend consistency | Adopted | Badge uses existing Tailwind/shadcn token; follows existing filter panel pattern |
| P4 - Migration | Deferred | Fresh DB gets the column via `create_all()`; existing DBs need manual ALTER TABLE; Alembic migration deferred (out of scope, academic project) |

### Trade-offs

- **Sentinel vs nullable**: Sentinel avoids schema migration and keeps `NOT NULL` guarantee. Downside: sentinel must be filtered out in ReportType listings for citizens. Mitigation: `ReportTypeModel.active` remains True but the sentinel id `"unknown"` is a known magic value -- use `filter_sentinel=True` query param if needed later.
- **Synchronous suggestion vs async**: Synchronous is simpler and correct for the current volume (local ChromaDB, <5k reports). DistilBERT CPU inference adds ~50-200ms per request -- acceptable for academic context.
- **Single PATCH vs general PATCH**: Narrow `PATCH /reports/{id}/report-type` is safer (explicit role + field restriction) over a general `PATCH /reports/{id}`.

---

## Test Plan

1. Fresh DB: run `uv run kb-qa ingest` (if applicable) + `uv run python scripts/seed_all.py`; verify sentinel `ReportType` appears in `/report-types` response
2. `POST /reports` without `report_type_id` -> 201 with `report_type_source: "ai_suggested"` or sentinel
3. `POST /reports` with `report_type_id` -> 201 with `report_type_source: "citizen"`
4. `GET /reports/{id}/suggest-type` -> 200 `SuggestionResponse` with non-empty `suggestions`
5. `PATCH /reports/{id}/report-type` as citizen -> 403
6. `PATCH /reports/{id}/report-type` as agent -> 200 with `report_type_source: "agent_override"`
7. `/reports/query` with `awaiting_type_review: true` -> only AI-suggested or sentinel reports returned
8. Frontend: report with `report_type_source === "ai_suggested"` shows "IA" badge
9. Switch `FALA_GAVEA_SUGGESTION_BACKEND=distilbert`; restart server; repeat steps 2-4 (if model present); verify `backend: "distilbert"` in suggest response
