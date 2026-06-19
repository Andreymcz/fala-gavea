# Progress -- Plan 000099

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Codebase Patterns

- `SemanticConfig` lives in `src/fala_gavea/infrastructure/embeddings/registry.py` — `embed_model_topics` defaults to `paraphrase-multilingual-MiniLM-L12-v2`
- `bertopic>=0.17` was already in `pyproject.toml` (no `uv add` needed)
- `BERTopic.get_topic()` returns `False | list[tuple[str, float]]` — must isinstance-guard before iterating
- CONVENTION_1 enforced: `bertopic` import is scoped inside `infrastructure/topics/bertopic_client.py` only

## Iteration Log

### 2026-06-19 — Steps 1-4 (port, client, use case, schema)

- Step 1: Added `infer_topics(reports)` abstract method to `ITopicModelPort` in `semantic_ports.py`
- Step 2: Created `src/fala_gavea/infrastructure/topics/bertopic_client.py` with `BERTopicClient`; `fit`, `topic_of`, `list_topics` raise `NotImplementedError`
- Step 3: Created `src/fala_gavea/application/use_cases/topics/get_topics_for_reports.py` with `GetTopicsForReports.execute()`
- Step 4: Created `src/fala_gavea/presentation/schemas/topic.py` with `TopicItem` and `TopicListResponse`
- Verification: ruff clean, pyright 0 errors on new files (49 pre-existing errors in other files unchanged)
- Commit: `eb33216`

### 2026-06-19 — Steps 5-7 (dependency provider, endpoint, tests)

- Step 5: Added `get_topic_model_port()` lazy singleton to `dependencies.py`; follows same pattern as `get_report_indexer`; imports `BERTopicClient` and `SemanticConfig` lazily; returns `None` on error
- Step 6: Added `GET /reports/topics` endpoint in `reports.py` before `GET /{id}`; reuses `ReportFiltersQuery` + `ReportFilters`; returns 503 if port=None, 200 with empty list if too few reports, otherwise calls `GetTopicsForReports`
- Step 7: Created `tests/test_topic_modeling.py` with 6 tests — all pass; fixed `ReportStatus.open` -> `ReportStatus.pendente` (enum value mismatch found during run)
- Commit: `750d1a2`
