# QA Log — plan | 000096 | Dockerfile + Railway deploy

**Brief:** folowing research 91 lets create a dockerfile to install and run the app locally, preparing to publish the app into Railway. create a mappiong to the db storage to local file

**Session:** 2026-06-19 17:11 UTC → 2026-06-19 17:14 UTC

## Planning decisions

- Multi-stage Dockerfile (Node 22 + Python 3.13-slim) per research-000091 recommendation.
- Railway chosen as deploy platform (persistent volume, no sleep on free tier).
- ChromaDB in-process; `CHROMA_DATA_DIR` env var routes data to `/data/chromadb` on Railway volume.
- `DATABASE_URL=sqlite:////data/fala_gavea.db` (absolute path to mounted volume).
- Win32 `required-environments` constraint in `pyproject.toml` must be removed as Step 1.
- Ollama graceful degradation (HTTP 503) when `FALA_GAVEA_OLLAMA_URL` unset.
- `/health` endpoint added for Railway health checks.
- Docker Compose deferred (single-container stack is sufficient for current PoC).
