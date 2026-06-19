# Plan 000096 | CHORE -O | 2026-06-19 17:15 UTC | Dockerfile + Railway deploy | Review: light
plan_format_version: 1

## Brief

Following research-000091: create a Dockerfile to build and run the app locally and on Railway; mount the SQLite database to a local persistent volume so data survives redeployments.

## Context

- Stack: FastAPI + SQLite/SQLAlchemy + ChromaDB (in-process) + React SPA served via FastAPI StaticFiles.
- `static/` is the SPA output directory (`frontend/dist → static/`), resolved at 4 parents above `main.py`.
- `DATABASE_URL` is already env-var driven (default `sqlite:///./fala_gavea.db`).
- **Blocker:** `pyproject.toml` declares `required-environments = ["sys_platform == 'win32' ..."]` — this must be removed so `uv sync` works inside a Linux container.
- ChromaDB runs in-process (no separate container needed yet); its data directory must also be persisted.
- Ollama (`qwen3:8b`) cannot run in cloud — needs graceful degradation when `FALA_GAVEA_OLLAMA_URL` is unset.

## Complexity: Low → Review depth: light

---

## Steps

### Step 1 — Remove the win32-only `required-environments` constraint from `pyproject.toml`

**File:** `pyproject.toml`

**Why:** The `[tool.uv]` section currently restricts installs to `sys_platform == 'win32'`, which makes `uv sync` fail inside a Linux Docker container (the standard Railway runtime).

**What to do:**

Delete this block entirely from `pyproject.toml`:

```toml
[tool.uv]
required-environments = ["sys_platform == 'win32' and platform_machine == 'AMD64'"]
```

Run `uv lock` locally after this edit to update the lockfile for a cross-platform environment.

```
Validation: uv sync --frozen --no-dev succeeds without error on a clean venv.
Docs: none
```

---

### Step 2 — Create `Dockerfile` at project root

**File:** `Dockerfile` (new, project root)

**Why:** Multi-stage build keeps the final image lean (no Node.js toolchain) and follows the research recommendation.

**Content:**

```dockerfile
# Stage 1: Build React SPA
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# outputs to /app/frontend/dist/

# Stage 2: Python runtime
FROM python:3.13-slim AS runtime

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python dependencies from lockfile (production only)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy pre-built SPA into static/ (the path main.py resolves to)
COPY --from=frontend-build /app/frontend/dist ./static/

# Data directory for persistent volume mount
RUN mkdir -p /data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "fala_gavea.presentation.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

Key decisions:
- `/data` is created empty in the image; Railway mounts the persistent volume here at runtime.
- `DATABASE_URL` and `CHROMA_DATA_DIR` are injected via env vars — never hardcoded.
- No `.env` file is copied into the image.

```
Validation: docker build -t fala-gavea . completes without error.
Docs: none
```

---

### Step 3 — Create `.dockerignore`

**File:** `.dockerignore` (new, project root)

**Why:** Prevents the build context from including the local SQLite DB, vector store, node_modules, `__pycache__`, and other large/sensitive files.

**Content:**

```
__pycache__/
*.pyc
*.pyo
.venv/
.pytest_cache/
.ruff_cache/
node_modules/
frontend/node_modules/
frontend/dist/
frontend/.env*
static/
knowledge/vectorstore/
*.db
*.sqlite
.env
.env.*
!.env.example
_output/
.git/
```

```
Validation: docker build context size is reasonable (under ~200 MB).
Docs: none
```

---

### Step 4 — Update `.env.example` with all runtime env vars

**File:** `.env.example`

**Why:** Serves as documentation for developers and as the reference when configuring Railway Variables.

**Replace content with:**

```bash
# --- Database ---
# Local: sqlite:///./fala_gavea.db  (relative to working dir)
# Railway: sqlite:////data/fala_gavea.db  (absolute path to mounted volume)
DATABASE_URL=sqlite:///./fala_gavea.db

# --- Auth ---
JWT_SECRET=change-me-in-production

# --- Ollama (optional) ---
# Leave unset to disable NL chat gracefully
FALA_GAVEA_OLLAMA_URL=http://localhost:11434
FALA_GAVEA_OLLAMA_MODEL=qwen3:8b

# --- ChromaDB ---
# Local: leave unset (defaults to ./chroma_data)
# Railway: /data/chromadb
CHROMA_DATA_DIR=/data/chromadb
```

```
Validation: .env.example committed; real values never committed.
Docs: none
```

---

### Step 5 — Make ChromaDB data directory configurable via `CHROMA_DATA_DIR`

**Files:** `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py`, `src/fala_gavea/infrastructure/embeddings/registry.py` (or wherever `chromadb.PersistentClient` is instantiated)

**Why:** The in-process ChromaDB client writes its index to a local directory. On Railway, that directory must be under `/data/chromadb` (the persistent volume). The path must be env-var driven, not hardcoded.

**What to do:**

1. Locate all calls to `chromadb.PersistentClient(path=...)` or `chromadb.Client(...)`.
2. Replace the hardcoded path with:
   ```python
   import os
   CHROMA_DATA_DIR = os.environ.get("CHROMA_DATA_DIR", "./chroma_data")
   client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
   ```
3. Ensure the directory is created at startup if it does not exist (ChromaDB does this automatically for `PersistentClient`, but add an explicit `os.makedirs` for clarity).

```
Validation: uv run pytest passes; CHROMA_DATA_DIR env var is respected.
Docs: none
```

---

### Step 6 — Add `/health` endpoint to FastAPI

**File:** `src/fala_gavea/presentation/api/main.py`

**Why:** Railway (and all PaaS platforms) uses a health-check HTTP call to determine whether the container is running. Without it, deploys may be flagged as failed even when the app is healthy.

**What to do:**

Add to `create_app()` before `_mount_spa(app)`:

```python
from fastapi.responses import JSONResponse

@app.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
```

```
Validation: curl http://localhost:8000/health returns {"status":"ok"}.
Docs: none
```

---

### Step 7 — Implement graceful degradation when Ollama is unavailable

**File:** `src/fala_gavea/infrastructure/ollama/` (OllamaClient or equivalent)

**Why:** `qwen3:8b` cannot run in a cloud container. When `FALA_GAVEA_OLLAMA_URL` is unset or unreachable, the NL chat feature must fail gracefully with a clear message rather than a 500 error.

**What to do:**

1. In `OllamaClient.__init__` (or wherever the client connects), check if `FALA_GAVEA_OLLAMA_URL` is set. If not, set `self._available = False`.
2. On any method call when `_available is False`, raise an application-level exception (e.g., `OllamaUnavailableError`) instead of a network error.
3. In the router/use-case that calls the Ollama client, catch `OllamaUnavailableError` and return HTTP 503 with body `{"detail": "NL chat is unavailable in this deployment."}`.

```
Validation: With FALA_GAVEA_OLLAMA_URL unset, the NL chat endpoint returns 503 (not 500); all other endpoints work normally.
Docs: none
```

---

### Step 8 — Local smoke test: build and run the container

**Why:** Validates the Dockerfile and environment wiring before deploying to Railway.

**Commands to run locally:**

```bash
# Build
docker build -t fala-gavea .

# Run with a local volume for persistence
docker run -p 8000:8000 \
  -v "$(pwd)/local-data:/data" \
  -e DATABASE_URL=sqlite:////data/fala_gavea.db \
  -e CHROMA_DATA_DIR=/data/chromadb \
  -e JWT_SECRET=local-dev-secret \
  fala-gavea

# Verify
curl http://localhost:8000/health
open http://localhost:8000
```

```
Validation: App is reachable at localhost:8000; /health returns 200; SPA loads.
Docs: none
```

---

### Step 9 — Add `railway.json` (Railway deploy config)

**File:** `railway.json` (new, project root)

**Why:** Declares the build and start commands, health check path, and port for Railway's build system. Avoids relying on platform auto-detection.

**Content:**

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uv run uvicorn fala_gavea.presentation.api.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

Note: Railway injects `$PORT` automatically; the CMD in Dockerfile uses `8000` as a local fallback.

```
Validation: railway up succeeds; Railway dashboard shows service healthy.
Docs: none
```

---

### Step 10 — Document Railway deployment steps in README (brief)

**File:** `README.md` (or create one if absent)

**Why:** Team members need to know the required Railway Variables and volume configuration.

**Add a "Deploy to Railway" section:**

```markdown
## Deploy to Railway

1. Create a new Railway project and link this repo.
2. Add a **Volume** in the service settings, mounted at `/data`.
3. Set **Variables** in the Railway dashboard:
   - `DATABASE_URL=sqlite:////data/fala_gavea.db`
   - `CHROMA_DATA_DIR=/data/chromadb`
   - `JWT_SECRET=<strong random string>`
   - (Optional) `FALA_GAVEA_OLLAMA_URL` — omit to disable NL chat
4. Deploy. The `/health` endpoint is used for health checks.
```

```
Validation: README section committed.
Docs: none
```

---

## File Change Summary

| File | Action |
|------|--------|
| `pyproject.toml` | Remove `[tool.uv] required-environments` (Win32-only lock) |
| `uv.lock` | Regenerate after removing env restriction |
| `Dockerfile` | Create (multi-stage: Node 22 build + Python 3.13-slim runtime) |
| `.dockerignore` | Create |
| `.env.example` | Update with all env vars (DB, JWT, Ollama, ChromaDB) |
| `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` | Use `CHROMA_DATA_DIR` env var for persistence path |
| `src/fala_gavea/presentation/api/main.py` | Add `/health` endpoint |
| `src/fala_gavea/infrastructure/ollama/` | Graceful degradation when `FALA_GAVEA_OLLAMA_URL` unset |
| `railway.json` | Create (Railway deploy config) |
| `README.md` | Add "Deploy to Railway" section |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `uv.lock` may not resolve cross-platform after removing the env restriction | Run `uv lock` locally and commit the updated lockfile before building the Docker image |
| ChromaDB path hardcoded in multiple places | Grep for `chromadb.PersistentClient` and `chromadb.Client` in `infrastructure/` to catch all occurrences |
| Railway volume not mounted → SQLite at ephemeral path | Health check + Railway deploy logs will reveal missing data on restart; documented in README |
| sentence-transformers model download at container startup (slow) | Acceptable for PoC; future work: bake model into image with `COPY` |
