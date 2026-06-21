# Stage 1: Build React SPA
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# outputs to /app/static/ (vite.config outDir: "../static")

# Stage 2: Python runtime
FROM python:3.13-slim AS runtime

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install Python dependencies from lockfile (production only)
COPY pyproject.toml uv.lock ./
ENV UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN uv sync --frozen --no-dev

# Pre-download sentence-transformers model so runtime never hits HuggingFace
ENV HF_HOME=/app/.hf_cache
RUN uv run python -c \
  "from sentence_transformers import SentenceTransformer; \
   SentenceTransformer('intfloat/multilingual-e5-small')"

# Copy application source
COPY src/ ./src/
COPY scripts/ ./scripts/

# Copy pre-built SPA into static/ (the path main.py resolves to)
COPY --from=frontend-build /app/static/ ./static/

# Data directory for persistent volume mount
RUN mkdir -p /data

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "fala_gavea.presentation.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
