# Plan 000115 QA | CHORE -O | 2026-06-20 23:55 UTC | Railway deploy fixes

## Brief

aplicar correções de deploy Railway: JWT_SECRET_KEY em .env.example, DATABASE_URL absoluto, /health com DB probe, remover frontend/dist/ do .dockerignore. source: research-000114

## Q&A Log

**Q1 (user):** sim, gere um plan para aplicar todas as correções

**A1 (agent):** Gerado plan-000115 com 4 steps:
1. `.env.example`: corrigir `JWT_SECRET` → `JWT_SECRET_KEY`
2. `.env.example`: ampliar comentário do `DATABASE_URL` com aviso Railway
3. `main.py`: enriquecer `/health` com probe SQLite (`SELECT 1`, 503 em falha)
4. `.dockerignore`: remover entrada morta `frontend/dist/`
