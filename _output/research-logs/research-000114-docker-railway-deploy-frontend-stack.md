# Research 000114 | CHORE -O | 2026-06-20 23:46 UTC | Docker Railway deploy vs frontend stack changes
tags: docker, railway, deploy, frontend, security

## User Brief

Como a atual configuração docker está adequada a fazer o deploy no railway, considerando modificações recentes na stack tecnológica do front end. Segue plano 96.

## Agent Interpretation

Avaliar se o Dockerfile + railway.json (criados pelo plan-000096) ainda estão corretos e completos após as mudanças de frontend introduzidas nos plans 104, 112 e 113 (React SPA com Vite + TS + Tailwind + Radix UI + Leaflet + Zustand + TanStack Query + admin panel). Identificar gaps ou riscos antes de um deploy real no Railway.

## Files Reviewed

- `Dockerfile`
- `railway.json`
- `.dockerignore`
- `.env.example`
- `frontend/vite.config.ts`
- `frontend/package.json`
- `src/fala_gavea/config.py`
- `src/fala_gavea/infrastructure/auth/jwt_service.py`
- `src/fala_gavea/presentation/api/main.py`
- `_output/plans/plan-000096-dockerfile-railway-deploy.md`

---

## Q&A Log

### Q1

**Q:** Como a atual configuração docker está adequada a fazer o deploy no railway, considerando modificações recentes na stack tecnológica do front end. Segue plano 96.

**A:**

### Resumo da situação

O Dockerfile e o `railway.json` estão **funcionalmente corretos** para as mudanças recentes de frontend — todos os novos pacotes npm (Zustand, TanStack Query, Radix UI, react-leaflet) são resolvidos pelo `npm ci` existente, sem necessidade de alterar o Dockerfile. O `outDir: "../static"` do vite.config.ts e o `COPY --from=frontend-build /app/static/ ./static/` do Dockerfile estão alinhados (a discrepância do plan-000096 original — que previa `/app/frontend/dist` — foi corrigida na implementação).

No entanto, foram identificadas **duas falhas sérias** que precisam ser corrigidas antes do primeiro deploy real:

---

### Findings detalhados por perspectiva

| Perspectiva | Status | Resumo |
|-------------|--------|--------|
| Compatibilidade (frontend) | ✅ OK | outDir → `/app/static/` está correto. VITE_API_URL default `""` funciona. Todos os novos deps em package.json. |
| Performance / imagem | ✅ OK | Multi-stage correto, dev deps excluídos (`uv sync --no-dev`). `npm ci` determinístico. |
| Segurança | ⚠️ ISSUE | `JWT_SECRET` vs `JWT_SECRET_KEY` — mismatch silencioso entre `.env.example` e `config.py` |
| Operações / dados | ⚠️ CONCERN | `DATABASE_URL` padrão aponta para diretório efêmero; silencia perda de dados no Railway |
| DX / observabilidade | ⚠️ CONCERN | Health check não prova DB; `.dockerignore` tem entrada morta |

---

### Problema 1 — ALTO: mismatch JWT_SECRET / JWT_SECRET_KEY

**O que acontece:** `src/fala_gavea/config.py` lê `os.environ.get("JWT_SECRET_KEY", "change-me")`. O `.env.example` documenta `JWT_SECRET=change-me-in-production`. Um deployer que copia o exemplo para o Railway Variables nunca define `JWT_SECRET_KEY` — a aplicação sobe silenciosamente com o segredo `"change-me"`, assina tokens reais com ele, e a guard `if not config.JWT_SECRET_KEY` não dispara porque `"change-me"` é truthy.

**Fix:** Corrigir `.env.example` para usar `JWT_SECRET_KEY=change-me-in-production`.

---

### Problema 2 — ALTO: perda silenciosa de dados (DATABASE_URL padrão)

**O que acontece:** O default `sqlite:///./fala_gavea.db` resolve para o diretório de trabalho do container (`/app/fala_gavea.db`). No Railway, containers são efêmeros — sem o volume persistente montado em `/data` e `DATABASE_URL=sqlite:////data/fala_gavea.db` configurado nas Variables, cada redeploy apaga o banco silenciosamente.

**Fix:** Documentar claramente no `.env.example` qual o valor Railway correto (4 barras — caminho absoluto) e de preferência adicionar um aviso de startup quando `DATABASE_URL` for relativo em ambiente não-dev.

---

### Outros itens (menor prioridade)

**Health check superficial (MÉDIO):** `/health` retorna `{"status": "ok"}` incondicional, sem verificar conectividade com o banco. O Railway considera o deploy bem-sucedido mesmo que o SQLite não consiga abrir o arquivo. Adicionar `db.execute(text("SELECT 1"))` aumenta a confiabilidade da detecção de falhas durante redeploys.

**`.dockerignore` entrada morta (BAIXO):** `frontend/dist/` nunca é criado (o Vite gera em `../static`). Entrada harmless mas confusa para quem mantém o arquivo.

---

## Recomendações

| Prioridade | Ação | Arquivo |
|-----------|------|---------|
| HIGH | Corrigir `JWT_SECRET` → `JWT_SECRET_KEY` em `.env.example` | `.env.example` |
| HIGH | Documentar/alertar sobre `DATABASE_URL` relativo no Railway | `.env.example`, opcionalmente `config.py` |
| MEDIUM | Enriquecer `/health` para provar SQLite | `src/fala_gavea/presentation/api/main.py` |
| LOW | Remover `frontend/dist/` do `.dockerignore` | `.dockerignore` |

---

## Avaliação geral

O Dockerfile está **pronto para deploy** em relação às mudanças de frontend. Os problemas encontrados são de **configuração de deployment**, não de build ou compatibilidade de stack. O risco maior é a silenciosidade de ambas as falhas: JWT errado e dados perdidos são difíceis de diagnosticar depois do deploy. A correção é simples e urgente.
