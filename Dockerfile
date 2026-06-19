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
