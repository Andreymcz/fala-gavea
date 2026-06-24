# QA Log | Plan 000167 | 2026-06-24 19:31 UTC | performance: startup warm-up, thread-safe singleton, DB index

**Brief**: Diagnosed slow `/reports/query` responses on app open (4 parallel requests, seconds of latency). Root causes: lazy ChromaSearchClient initialization (cold-start), non-thread-safe singleton (race condition under concurrent load), missing `reports.created_at` DB index. Three targeted fixes applied inline then formalized as plan-000167.

---

## Q1

the query is slow. when i open the app some seconds passes. the server log:
```
INFO: 127.0.0.1:58310 - "POST /reports/query HTTP/1.1" 200 OK
INFO: 127.0.0.1:55065 - "POST /reports/query HTTP/1.1" 200 OK
INFO: 127.0.0.1:64303 - "POST /reports/query HTTP/1.1" 200 OK
INFO: 127.0.0.1:58309 - "POST /reports/query HTTP/1.1" 200 OK
```

## A1

Diagnosed two root causes:

1. **Cold start**: `ChromaSearchClient` (loads `SentenceTransformer`) is initialized lazily on the first HTTP request. All 4 parallel requests from the frontend hit this simultaneously on every server restart.
2. **Race condition**: `get_report_indexer()` had no lock — 4 concurrent threads could all pass `if _indexer_instance is None:` and attempt concurrent model loading.
3. **Missing DB index**: `reports.created_at` (default `ORDER BY` column) had no index — full-table scan on each `/reports/query` call.

Applied three fixes inline:
- `dependencies.py`: double-checked locking with `threading.Lock`
- `main.py`: `@app.on_event("startup")` to eagerly warm up ChromaSearchClient at boot
- `session.py`: `CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports (created_at DESC)`

---

## Q2

/plan plan fixes

## A2

Ran `/plan` skill. Mode auto-detected as single plan (targeted perf fix).

Reserved plan ID 000167. Wrote `_output/plans/plan-000167.md` with:
- Brief explaining 3 root causes
- Steps 1–3 documenting the 3 inline fixes (already implemented)
- Light review covering correctness, thread safety, DB indexing, and deferred items (LLM client lock, additional column indexes)
- Commit message draft

---

## Q3

run post skill

## A3

Running `/post-skill 167`. Executing pipeline: marked brief DONE, filed eager implement pending entry (pa-000059), writing QA log, then committing.
