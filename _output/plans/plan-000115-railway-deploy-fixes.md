# Plan 000115 | CHORE -O | 2026-06-20 23:54 UTC | Railway deploy fixes | Review: light
plan_format_version: 1
source: research-000114

## Brief

Aplicar as 4 correções de deploy Railway identificadas no research-000114:
1. `.env.example` usa `JWT_SECRET` mas `config.py` lê `JWT_SECRET_KEY` — mismatch silencioso
2. `DATABASE_URL` padrão aponta para caminho efêmero no Railway — perda silenciosa de dados
3. `/health` retorna OK sem provar o banco — Railway não detecta containers quebrados
4. `frontend/dist/` no `.dockerignore` é entrada morta (build vai para `../static`)

## Context

- `config.py` lê `os.environ.get("JWT_SECRET_KEY", "change-me")`
- `.env.example` documenta `JWT_SECRET=change-me-in-production` — deployer nunca seta a chave certa
- `DATABASE_URL` default `sqlite:///./fala_gavea.db` = caminho relativo no container; sem volume Railway → wipe a cada redeploy
- `/health` em `main.py` retorna `{"status": "ok"}` incondicional
- `SessionLocal` está em `src/fala_gavea/infrastructure/database/session.py` (SQLAlchemy sessionmaker)
- `.dockerignore` tem `frontend/dist/` mas Vite gera em `../static`, nunca em `dist/`

## Complexity: Low → Review depth: light

---

## Steps

### Step 1 — Corrigir `JWT_SECRET` → `JWT_SECRET_KEY` em `.env.example`

**File:** `.env.example`

**Why:** `config.py` lê `JWT_SECRET_KEY`; o `.env.example` documenta `JWT_SECRET`. Um deployer que copia o arquivo nunca define a variável correta e a aplicação sobe com `"change-me"` como segredo JWT sem nenhum aviso.

**Change:**
```diff
-JWT_SECRET=change-me-in-production
+JWT_SECRET_KEY=change-me-in-production
```

Manter o comentário existente `# --- Auth ---` acima.

```
Validation: grep "JWT_SECRET_KEY" .env.example retorna resultado; grep "^JWT_SECRET=" .env.example retorna vazio.
Docs: none
```

---

### Step 2 — Documentar `DATABASE_URL` para Railway no `.env.example`

**File:** `.env.example`

**Why:** O default `sqlite:///./fala_gavea.db` (3 barras = caminho relativo) resolve para o diretório de trabalho do container efêmero. No Railway, o volume persistente é montado em `/data` — o valor correto é `sqlite:////data/fala_gavea.db` (4 barras = caminho absoluto). Sem essa documentação clara, um deployer não sabe que precisa configurar a variável.

**Change:** Expandir o bloco `# --- Database ---` para deixar explícito qual valor usar no Railway:
```
# --- Database ---
# Local: sqlite:///./fala_gavea.db  (caminho relativo ao diretório de trabalho)
# Railway: sqlite:////data/fala_gavea.db  (caminho absoluto no volume persistente /data)
#   IMPORTANTE: sem DATABASE_URL configurado no Railway, dados são perdidos a cada redeploy.
DATABASE_URL=sqlite:///./fala_gavea.db
```

Obs: o comentário Railway já existe parcialmente — ampliar com a linha IMPORTANTE.

```
Validation: .env.example contém a linha "IMPORTANTE:" no bloco Database.
Docs: none
```

---

### Step 3 — Enriquecer `/health` com probe do banco

**File:** `src/fala_gavea/presentation/api/main.py`

**Why:** O Railway usa o health check HTTP para decidir se o container está saudável e pode receber tráfego. O endpoint atual retorna 200 incondicional — um container com o banco inacessível (volume não montado, arquivo corrompido) é tratado como saudável. Adicionar uma query SQLite mínima transforma o endpoint num detector real de falhas.

**What to do:** Substituir o health endpoint em `create_app()`:

```python
from sqlalchemy import text

@app.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        return JSONResponse({"status": "error", "detail": "db unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})
```

Adicionar `text` ao import de `sqlalchemy` existente. `SessionLocal` já é importado no arquivo.

```
Validation: uv run pytest passa; curl http://localhost:8000/health retorna {"status":"ok"} com DB disponível.
Docs: none
```

---

### Step 4 — Remover entrada morta `frontend/dist/` do `.dockerignore`

**File:** `.dockerignore`

**Why:** O Vite está configurado com `outDir: "../static"` — o build nunca gera `frontend/dist/`. A entrada é inócua mas confunde quem lê o arquivo esperando entender o que é excluído do contexto Docker.

**Change:** Remover a linha `frontend/dist/`.

```
Validation: cat .dockerignore não contém "frontend/dist/".
Docs: none
```

---

## File Change Summary

| File | Action |
|------|--------|
| `.env.example` | Fix `JWT_SECRET` → `JWT_SECRET_KEY`; ampliar comentário DATABASE_URL Railway |
| `src/fala_gavea/presentation/api/main.py` | `/health` prova SQLite com `SELECT 1`; retorna 503 se falhar |
| `.dockerignore` | Remover linha `frontend/dist/` (entrada morta) |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `/health` mais lento em ambientes de teste | SQLite `SELECT 1` é local e sub-ms; desprezível para healthcheck com timeout de 30s |
| Testes que mockam SessionLocal podem falhar no health probe | O teste do health deverá usar um DB em memória ou mockar a execução — verificar após a implementação |
| Deployer ainda precisa configurar `DATABASE_URL` no Railway manualmente | Documentação no `.env.example` é o único vetor possível sem CI enforcement |
