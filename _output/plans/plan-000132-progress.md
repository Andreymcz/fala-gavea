# Progress -- Plan 000132

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns
<!-- Subagents consolidate reusable patterns here -->

## Iteration Log

### Step 3 — 2026-06-21

Added `rank(query, ids) -> dict[str, float]` abstract method to `ISemanticSearchPort` in `semantic_ports.py`. Implemented in `ChromaSearchClient`: embeds query with `_encode_query`, fetches stored embeddings via `collection.get(ids=ids, include=["embeddings"])`, computes cosine similarity manually (dot product / product of norms), clamps to [0,1]. Formula is pure cosine (not the `1/(1+dist)` used in `search()`/`similar()` which convert L2 distance — `rank()` operates on arbitrary candidate sets without querying ChromaDB's ANN index). Pyright: 65 errors (all pre-existing, none introduced by these changes).

### Step 8 — 2026-06-21
Added cross-reference dependency note to plan-000131: FilterPanel/views now read through `POST /reports/query` (plan-000132); `useFilteredReports`/`useSemanticSearch` retargeted in Step 7; R2 catch-all guard remains independent.
