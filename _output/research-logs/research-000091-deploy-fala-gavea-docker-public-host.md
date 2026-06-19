# Research 000091 | CHORE -O | 2026-06-19 12:39 UTC | Deploy fala-gavea to public web host with Docker

tags: deployment, docker, infrastructure, ops, architecture

**User brief:** put fala-Gavea app into a open web url server. what are the hosts that allow a dockerfile to be deployed ? maybe we need to create a docker compose structure ?

**Agent interpretation:** Identify cloud platforms that support Dockerfile-based deployment for the fala-gavea FastAPI + React SPA stack; determine whether Docker Compose is needed now vs. later; design a minimal Dockerfile; address SQLite persistence and secrets management constraints for a student PoC demo.

**Files reviewed:** `pyproject.toml`, `frontend/package.json`, `product-design/project/product-design-as-coded.md`

---

## Q&A Log

### Q1

**User:** Which cloud hosting platforms support Dockerfile deployment for fala-gavea, and do we need Docker Compose?

**Answer:**

### Platform Landscape

| Platform | Free Tier | Persistent Volume | Sleep on Idle | Verdict |
|---|---|---|---|---|
| **Railway** | $5 trial credit | Yes (free) | No | **Best for PoC** |
| **Render** | Yes (spins down after 15 min) | Yes (paid $0.25/GB-mo) | Yes on free tier | Good; paid tier ($7/mo) removes sleep |
| **Fly.io** | 3 VMs + 3 GB free | Yes (free tier) | Configurable | Good if team knows Docker |
| **Google Cloud Run** | 2M req/month | No (stateless only) | Yes (scales to 0) | **NOT suitable** (SQLite needs volume) |
| **Hugging Face Spaces** | Yes | No | No | **NOT suitable** (ephemeral FS) |

**Recommendation: Railway** (lowest friction for SQLite + no sleep on free tier). Render is the backup but the free tier cold start (30-60 sec) is bad for a live demo.

---

### SQLite Persistence on Hosted Containers

The default container filesystem on every platform is **ephemeral** — every redeploy wipes the database.

**Fix:** Mount a persistent volume at `/data` and set `DATABASE_URL=sqlite:////data/fala_gavea.db` as a platform env var.

- **Railway:** Add a Volume to the service, mount at `/data`
- **Render:** Add a Persistent Disk ($0.25/GB-mo), mount at `/data` (note: disables zero-downtime deploys)
- **Fly.io:** `fly volumes create fala_data --size 1`, mount in `fly.toml`

---

### Secrets Management

Never write `ENV JWT_SECRET=...` in the Dockerfile. Never commit `.env` with real secrets. Use:
- Platform dashboard env vars (Railway Variables / Render Environment Variables / Fly.io `fly secrets set`)
- Commit only `.env.example` with placeholder values as documentation

---

### Docker Compose — When to Add It

**Not needed now.** The current stack (FastAPI + SQLite + React SPA) runs in a single container.

**Add Compose when ChromaDB is introduced as a separate container service.** At that point you need:
- `web` service (FastAPI)
- `chromadb` service (ChromaDB HTTP server)
- Named volume for ChromaDB data

**Shortcut:** Use ChromaDB as a Python library (in-process, not a server), storing its data directory under `/data/chromadb/`. This defers Compose until truly necessary and keeps the deployment simple for the PoC.

---

### Ollama / LLM in Cloud Deployment

`qwen3:8b` is ~5 GB and requires significant RAM. No free/cheap cloud tier can run it in-container.

Options:
1. **Graceful degradation** — when `FALA_GAVEA_OLLAMA_URL` is unset, disable the NL chat feature with a clear UI message. This is the correct approach for a PoC demo.
2. **External API substitution** — point `FALA_GAVEA_OLLAMA_URL` at a hosted Ollama-compatible API (Groq, OpenRouter). Requires API key management.

---

### Minimal Dockerfile

```dockerfile
# Stage 1: Build React SPA
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Outputs to frontend/dist/

# Stage 2: Python runtime
FROM python:3.13-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY scripts/ ./scripts/
# Pre-built SPA -> path FastAPI mounts as StaticFiles
COPY --from=frontend-build /app/frontend/dist ./static/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "fala_gavea.presentation.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

Key decisions:
- Multi-stage keeps the final image lean (no Node.js in production)
- `uv sync --frozen --no-dev` installs only production deps from lockfile
- `static/` must match the StaticFiles mount path in `main.py`
- `DATABASE_URL` injected via env var — not hardcoded in image

---

## Recommendations Summary

| Priority | Recommendation |
|---|---|
| HIGH | **Choose Railway** as the deployment platform; mount a persistent volume at `/data`; set `DATABASE_URL=sqlite:////data/fala_gavea.db` as env var |
| HIGH | **Write the Dockerfile** (multi-stage, as above) and commit it to the project root |
| HIGH | **Add `.env.example`** documenting all required env vars (JWT secret, DATABASE_URL, FALA_GAVEA_*); inject real values via platform secrets UI |
| MEDIUM | **Do not add Docker Compose yet** — add it only when ChromaDB runs as a separate server container |
| MEDIUM | **Plan for Ollama absence** — implement graceful degradation when `FALA_GAVEA_OLLAMA_URL` is unset |
| LOW | **Add a `/health` endpoint** to FastAPI returning `{"status": "ok"}` — needed for platform health checks |
