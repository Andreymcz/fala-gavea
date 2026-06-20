# Plan 000113 | feat/seed-relatos | 2026-06-20 22:35 UTC | Seed de Relatos no painel admin (CSV enriquecido) | Review: standard
plan_format_version: 1
source: plan-000112

## Context

O painel admin (`/admin`, plan-000112) hoje expõe apenas "Seed de Tópicos" e "Limpar Banco". Existe um endpoint backend `POST /admin/seed/relatos` (em [seed.py](../../src/fala_gavea/presentation/api/routers/seed.py)) que usa **o admin logado como autor de todos os relatos** e fixa `urgency=media`, lendo apenas as colunas `texto_relato, latitude, longitude, data, topico`. Nenhuma UI o expõe.

Este plano enriquece o seed de relatos para popular o banco de forma mais completa, com autoria por linha e fallbacks, e adiciona uma seção "Seed de Relatos" ao painel admin.

**Decisões travadas com o usuário (dev seed):**
- CSV header: `user_id, texto_relato, latitude, longitude, data, topico, urgency`.
- `user_id` é a **única coluna obrigatória**. Linha sem `user_id` → pulada com erro.
- **Autor por `user_id`, deduplicado:** e-mail sintético `{user_id}@seed.gavea.br`, name `Cidadão {user_id}`, role `citizen`, senha literal `changeme` (confirmado: ambiente de dev). Reusa conta existente pelo e-mail sintético.
- `topico` ausente no banco → **auto-cria** o ReportType (em vez do comportamento atual de pular).
- `latitude`/`longitude` ausente/inválida → **coordenada aleatória no bounding box da Gávea** (lat −22.975…−22.953, lon −43.235…−43.205 — mesmas constantes de [seed_relatos.py](../../scripts/seed_relatos.py)).
- `data` ausente/inválida → `created_at = now` (default de `Report.create`).
- `urgency` vazio/inválido → `media`.
- `texto_relato` → texto do relato.
- **Fora de escopo:** status variado, `photo_url`, encaminhamentos (forwardings), proteção de idempotência no endpoint (duplicar relatos em re-run é aceitável; só usuários são deduplicados).
- **Reuso de conta** pelo e-mail sintético nunca regrava a senha de um usuário existente — apenas contas recém-criadas recebem `changeme` (o caminho de reuso só lê `find_by_email`, não atualiza).

**Símbolos reaproveitados (já existem):** `IUserRepository.find_by_email/save`, `User.create(email, password_hash, name, role)`, `PasswordService.hash_password`, `IReportTypeRepository.find_by_name`, `CreateReportType(...).execute(nome, descricao)`, `Report.create(...)`, `Urgency`, deps `get_user_repo` / `get_password_service` / `get_report_type_repo` / `get_report_repo` / `get_report_indexer`, schema `SeedRelatosResponse`.

## Steps

### Step 1: Enriquecer o use case `BulkCreateReports`

Reescrever `execute` em [bulk_create_reports.py](../../src/fala_gavea/application/use_cases/reports/bulk_create_reports.py) para resolver autor por linha, auto-criar tópico e aplicar os fallbacks.

**Assinatura nova** (substitui o param `author_id` por dependências de user):
```python
def execute(
    self,
    rows: list[dict],
    report_type_repo: IReportTypeRepository,
    report_repo: IReportRepository,
    user_repo: IUserRepository,
    password_service: PasswordService,
    indexer: IReportIndexer | None = None,
) -> BulkResult:
```

**Constantes de módulo** (bounding box da Gávea, copiadas de `seed_relatos.py`):
```python
_LAT_MIN, _LAT_MAX = -22.975, -22.953
_LON_MIN, _LON_MAX = -43.235, -43.205
_DEFAULT_PASSWORD = "changeme"
```

**Lógica por linha** (índice `i`, **base 0** nos erros — manter o contrato atual de `BulkResult`/`SeedErrorItem`; não migrar para base 1):
1. `user_id = str(row.get("user_id", "")).strip()`; se vazio → `skipped += 1`, `errors.append({"row": i, "reason": "user_id obrigatório"})`, `continue`.
2. **Resolver/criar autor** (com cache local `author_cache: dict[str, str]` user_id→user.id para evitar lookups repetidos):
   - `email = f"{user_id}@seed.gavea.br"`.
   - se `user_id` no cache → usa; senão `user = user_repo.find_by_email(email)`; se `None` → `user = User.create(email=email, password_hash=password_service.hash_password(_DEFAULT_PASSWORD), name=f"Cidadão {user_id}", role=UserRole.citizen)` e `user_repo.save(user)`. `author_cache[user_id] = user.id`.
3. **Tópico** (`topico = str(row.get("topico", "")).strip()`): se vazio → skip com erro `"topico obrigatório"`. Senão `rt = report_type_repo.find_by_name(topico)`; se `None`, auto-cria **com guarda** (o validador de `CreateReportType` exige 3–100 chars e lança `InvalidInputError`; sem a guarda, um tópico de <3 chars aborta todo o batch com 500):
   ```python
   rt = report_type_repo.find_by_name(topico)
   if rt is None:
       try:
           rt = CreateReportType(report_type_repo).execute(topico, None)  # usar o retorno direto
       except InvalidInputError:
           skipped += 1
           errors.append({"row": i, "reason": f"topico inválido: {topico!r}"})
           continue
   ```
   Usar o `ReportType` retornado por `execute` diretamente (sem re-fetch via `find_by_name`).
4. **Coordenadas**: tentar `lat = float(row["lat"])`, `lon = float(row["lon"])`; em `KeyError/TypeError/ValueError` (ausente/vazia/inválida) → `lat = round(random.uniform(_LAT_MIN, _LAT_MAX), 6)`, `lon = round(random.uniform(_LON_MIN, _LON_MAX), 6)` (não pular mais a linha por coordenada).
5. **Data**: manter o parse atual de `row.get("data")` → `datetime`; em falha → `created_at = None` (Report.create usa `now`).
6. **Urgency**: `raw = str(row.get("urgency", "")).strip().lower()`; `urgency = Urgency(raw) if raw in {"alta","media","baixa"} else Urgency.media`.
7. `text = str(row.get("descricao", "")).strip()`.
8. `Report.create(text=text, lat=lat, lon=lon, urgency=urgency, report_type_id=rt.id, author_id=author_cache[user_id], created_at=created_at)`; `report_repo.save(report)`; `inserted += 1`; indexar como hoje (try/except com warning).

Imports novos no arquivo: `random`, `User`, `UserRole`, `IUserRepository`, `PasswordService`, `CreateReportType`, `InvalidInputError`.

- **Files**: `src/fala_gavea/application/use_cases/reports/bulk_create_reports.py` (modify), `tests/test_bulk_create_reports.py` (modify)
- **References**: `project/standards.md § Backend`, `project/security-checklists.md`
- **Tests**: **`tests/test_bulk_create_reports.py` já existe com ~10 testes que chamam a assinatura ANTIGA posicionalmente (`execute(rows, "user-1", report_type_repo, report_repo)`) e dois que codificam comportamento agora inválido (`test_skips_unknown_topico` — tópico agora é auto-criado; `test_urgency_is_always_media` — urgency agora vem do CSV). REESCREVER, não estender:** atualizar o helper de fakes para também fornecer `user_repo` (fake com `find_by_email`→`None` na 1ª vez, registrando os `save` para checar dedup) e `password_service` fake; corrigir todas as chamadas para a nova assinatura por keyword; remover/substituir os dois testes contraditórios. Casos a cobrir: (a) auto-cria usuário quando `user_id` novo e reusa no 2º relato do mesmo `user_id` (apenas 1 save de user); (b) `user_id` vazio → linha pulada com erro (índice base-0); (c) tópico inexistente é auto-criado e o relato referencia o novo ReportType; (d) tópico com <3 chars → linha pulada com erro, batch **não** aborta; (e) urgency lida do CSV e fallback `media` para valor inválido; (f) lat/lon ausente → coordenada gerada dentro do bbox da Gávea. Padrão de fakes: estender o `_make_repos` existente (MagicMock) para retornar também `user_repo` (`find_by_email.return_value = None`, `save.side_effect = lambda u: u`) e `password_service` (`hash_password.return_value = "hashed"`); para o caso de auto-criação de tópico, configurar `find_by_name.return_value = None` e checar que `report_type_repo.save` foi chamado.
- **Verify**: `uv run pytest tests/test_bulk_create_reports.py` passa; `uv run pyright src/` sem novos erros.
- [ ] Done

### Step 2: Atualizar o endpoint `POST /admin/seed/relatos`

Em [seed.py](../../src/fala_gavea/presentation/api/routers/seed.py), `seed_relatos`: parsear as colunas novas e injetar as dependências de user.

- Adicionar parâmetros de dependência: `user_repo: IUserRepository = Depends(get_user_repo)`, `password_service: PasswordService = Depends(get_password_service)` (imports já disponíveis em `dependencies.py`).
- Montar cada `row` com as chaves que o use case espera, lendo as colunas do CSV:
  ```python
  rows.append({
      "user_id": row.get("user_id", "") or row.get("id_cidadao", ""),
      "descricao": row.get("texto_relato", ""),
      "lat": row.get("latitude", ""),
      "lon": row.get("longitude", ""),
      "data": row.get("data", ""),
      "topico": row.get("topico", ""),
      "urgency": row.get("urgency", ""),
  })
  ```
  (aceitar `id_cidadao` como alias de `user_id` para compatibilidade com os CSVs antigos.)
- Trocar a chamada para passar `user_repo` e `password_service` e **remover** `author_id=current_user.id`:
  ```python
  result = BulkCreateReports().execute(
      rows,
      report_type_repo=report_type_repo,
      report_repo=report_repo,
      user_repo=user_repo,
      password_service=password_service,
      indexer=indexer,
  )
  ```
- Manter `require_role("admin")`, a validação de content-type CSV e o `SeedRelatosResponse` (inserted/skipped/errors) inalterados.

- **Files**: `src/fala_gavea/presentation/api/routers/seed.py` (modify)
- **References**: `project/standards.md § Backend`, `project/security-checklists.md`
- **Depends on**: Step 1
- **Tests**: teste de endpoint (TestClient, padrão de `tests/test_bootstrap_admin.py`): admin envia CSV com `user_id` novo + tópico inexistente → 200 com `inserted >= 1`, usuário sintético criado, ReportType criado; CSV sem `user_id` → linha em `skipped`; não-admin → 403.
- **Verify**: `uv run pytest tests/ -k seed_relatos` passa.
- [ ] Done

### Step 3: Adicionar `seedRelatos` ao `api.ts`

Em [api.ts](../../frontend/src/lib/api.ts), adicionar método espelhando `seedTopicos` (multipart `fetch` + `FormData`, header Bearer, sem `Content-Type` manual):
```ts
seedRelatos(file: File): Promise<{ inserted: number; skipped: number; errors: unknown[] }> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${BASE_URL}/admin/seed/relatos`, { method: "POST", headers, body: formData }).then(
    async (res) => {
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new ApiError(res.status, data.detail || res.statusText);
      }
      return res.json();
    },
  );
},
```

- **Files**: `frontend/src/lib/api.ts` (modify)
- **References**: `project/standards.md § Frontend`
- **Verify**: `cd frontend && npx tsc --noEmit` limpo.
- [ ] Done

### Step 4: Adicionar card "Seed de Relatos" ao `AdminPage.tsx` (regras em pt-BR)

Em [AdminPage.tsx](../../frontend/src/features/admin/AdminPage.tsx), adicionar uma `<section>` "Seed de Relatos" **antes** (ou logo após) a de Tópicos, no mesmo padrão visual (card bordado `rounded-md border border-gray-200 p-5`). Estado próprio: `relatosFile`, `seedingRelatos` (reaproveitar o padrão de `handleSeedSubmit`/`seedTopicos`).

- Input `type="file" accept=".csv"` + botão "Enviar CSV"; ao submeter chama `api.seedRelatos(file)`; toast de sucesso `"X relatos inseridos, Y ignorados."`, toast de erro no catch (`err instanceof ApiError ? err.detail : ...`); limpar o input após sucesso.
- **Bloco de regras em pt-BR** (texto visível ao usuário descrevendo o formato), por exemplo:
  > Envie um CSV com as colunas `user_id, texto_relato, latitude, longitude, data, topico, urgency`. Apenas **user_id** é obrigatório. Regras automáticas:
  > - **Usuário:** se o `user_id` não existir, criamos uma conta de cidadão automaticamente (senha padrão de desenvolvimento).
  > - **Tópico:** se o tópico informado não existir, ele é criado.
  > - **Localização:** sem latitude/longitude válidas, geramos um ponto aleatório na Gávea.
  > - **Data:** sem data, usamos o momento da importação.
  > - **Urgência:** valores aceitos `alta`, `media`, `baixa`; vazio assume `media`.

- **Files**: `frontend/src/features/admin/AdminPage.tsx` (modify)
- **References**: `project/standards.md § Frontend`
- **Depends on**: Step 3
- **Tests**: estender [AdminPage.test.tsx](../../frontend/src/features/admin/AdminPage.test.tsx): mockar `api.seedRelatos`; caso "renderiza seção Seed de Relatos" e caso "upload de CSV chama seedRelatos(file)".
- **Verify**: `cd frontend && npm run test -- --run` verde; seção renderiza com as regras pt-BR.
- [ ] Done

## Review

**Depth: standard** (auto=standard: multi-camada model+API+UI **e** cria contas de autenticação automaticamente; floor=light; flag=none)

| Perspectiva | Achado | Status |
|---|---|---|
| P1 Security | Endpoint mantém `require_role("admin")`; backend impõe 403 independente do guard de UI. | Adopted |
| P1 Security | Contas auto-criadas usam senha padrão fixa `changeme` — **aceitável só em dev** (confirmado pelo usuário). Risco: se rodado em produção, cria contas logáveis com senha conhecida. Mitigação documentada no card pt-BR e no Context; não há flag de "must-reset" no modelo (fora de escopo). | Adopted (dev-only) |
| P0 Correctness | Autor resolvido por `user_id` com cache + dedup por e-mail sintético evita múltiplas contas para o mesmo `user_id`. | Adopted |
| P0 Correctness | Mudança de assinatura de `BulkCreateReports.execute` afeta apenas o endpoint `/relatos` (único chamador); ambos mudam juntos neste plano. | Adopted |
| P2 Simplicity | `seedRelatos` e o card reaproveitam exatamente o padrão de `seedTopicos`/seção de Tópicos — sem novas primitivas. | Adopted |
| P3 Consistency | Aceitar `id_cidadao` como alias de `user_id` mantém compatibilidade com os CSVs de `scripts/seeds/`. | Adopted |
| P0 Correctness (review F1) | Auto-criar tópico via `CreateReportType` lança `InvalidInputError` para nomes <3 chars; sem guarda, abortaria o batch (500). Step 1 envolve em try/except → skip+erro. | Adopted (amended) |
| P4 Testability (review F-TEST) | `tests/test_bulk_create_reports.py` (10 testes) quebra na nova assinatura; 2 testes codificam comportamento agora inválido. Step 1 reescreve o arquivo. | Adopted (amended) |
| P2 Simplicity (review F2) | Usar o retorno de `CreateReportType.execute` em vez de re-fetch via `find_by_name` (uma query a menos). | Adopted (amended) |
| P3 Consistency (review F4) | Índice de erro mantido em base-0 (contrato atual de `BulkResult`/`SeedErrorItem`), não base-1. | Adopted (amended) |
| P1 Security (review F-DoS) | Sem limite de tamanho de CSV / comprimento de texto. Aceitável para ferramenta admin-only de dev. | Deferred |

## Commit

```
feat(seed-relatos): seed de relatos no painel admin — CSV com user_id, auto-cria usuário/tópico e fallbacks Gávea
```
