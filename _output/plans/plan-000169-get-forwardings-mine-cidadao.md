# Plan 000169 | fala-gavea | 2026-06-24 20:00 UTC | GET /forwardings/mine — encaminhamentos do cidadão | Review: standard
plan_format_version: 1
source: research-000168

## Brief

GET /forwardings/mine — endpoint auth-required que retorna os encaminhamentos com relatos do cidadão logado. source: research-000168

## Context

O cidadão autenticado não tem endpoint direto para ver "todos os encaminhamentos que contêm pelo menos um dos meus relatos". A pesquisa 000168 avaliou 4 opções e recomendou criar `GET /forwardings/mine` (auth-required), usando `current_user.id` como filtro interno via JOIN em `forwarding_reports → reports`. A rota retorna `list[PublicForwardingResponse]` (sem `agent_id`) e é protegida por `get_current_user` — qualquer role (citizen, agent, admin) pode acessar.

`ForwardingFilters` **não recebe** `author_id` — esse dataclass pertence à superfície agent/admin. A filtragem é feita via novo método de repositório dedicado `find_by_author_id`.

## Scope

- **Backend:** 4 camadas (domain → infrastructure → application → presentation), 4 arquivos modificados + 1 novo
- **Frontend:** 3 arquivos modificados (api.ts, useForwardings.ts, PublicForwardingsPage.tsx)
- **Tests:** 3 novos casos de teste em `tests/test_forwardings.py`
- **Fora do escopo:** paginação, filtro de status no `/mine`, endereçar N+1 pré-existente nas listagens

## Review

**Review depth: standard** (auto=standard, floor=light, flag=none; efetivo=standard — feature cross-layer com novo método de repositório e nova rota)

### Perspectives

| Perspective | Status | Note |
|---|---|---|
| SEC | Adopted | `get_current_user` garante que somente usuários autenticados acessem; `current_user.id` nunca aparece na URL |
| ARCH | Adopted | Novo método de repo isolado; `ForwardingFilters` não alterado; use case novo espelha padrão existente |
| DATA | Adopted | `SELECT DISTINCT` previne duplicatas quando relato está em múltiplos encaminhamentos |
| UX | Adopted | Toggle "Meus encaminhamentos" visível só para usuários autenticados na `PublicForwardingsPage` |
| TEST | Adopted | 3 casos: happy path, exclusão de terceiros, 401 sem auth |
| PERF | Deferred | N+1 pré-existente nas listagens de encaminhamentos (cada item chama `GetForwarding`); escopo separado |

---

## Steps

### Step 1: Adicionar `find_by_author_id` à interface `IForwardingRepository`

Adicionar o método abstrato `find_by_author_id(author_id: str) -> list[Forwarding]` à classe `IForwardingRepository` em `forwarding_repository.py`. Este método representa a operação de busca reversa "quais encaminhamentos contêm relatos deste autor". Não alterar `ForwardingFilters` — o dataclass permanece vinculado à superfície agent/admin.

```python
@abstractmethod
def find_by_author_id(self, author_id: str) -> list[Forwarding]:
    """Return all forwardings that contain at least one report authored by author_id."""
```

- **Files**: `src/fala_gavea/domain/repositories/forwarding_repository.py` (modify)
- **Interface**: `IForwardingRepository.find_by_author_id(author_id: str) -> list[Forwarding]`
- **Verify**: `uv run pyright src/` passa sem erros relacionados ao método abstrato não implementado (após Step 2 ser concluído)
- **Tests**: Coberto pelos testes de API do Step 6
- [ ] Done

---

### Step 2: Implementar `find_by_author_id` no `SQLAlchemyForwardingRepository`

Implementar o método `find_by_author_id` em `SQLAlchemyForwardingRepository`. A query faz JOIN entre `forwardings → forwarding_reports → reports` e filtra por `reports.author_id = author_id`, usando `DISTINCT` para evitar duplicatas quando um relato está em múltiplos encaminhamentos.

```python
def find_by_author_id(self, author_id: str) -> list[Forwarding]:
    stmt = (
        select(ForwardingModel)
        .join(ForwardingReportModel, ForwardingReportModel.forwarding_id == ForwardingModel.id)
        .join(ReportModel, ReportModel.id == ForwardingReportModel.report_id)
        .where(ReportModel.author_id == author_id)
        .distinct()
    )
    return [self._to_entity(m) for m in self._session.scalars(stmt).all()]
```

Importar `ReportModel` de `fala_gavea.infrastructure.database.models` (já disponível no módulo).

- **Files**: `src/fala_gavea/infrastructure/repositories/sqlalchemy_forwarding_repository.py` (modify)
- **References**: `product-design/project/product-design-as-coded.md § 3` (padrão de join existente em `find_by_report_id`)
- **Depends on**: Step 1
- **Interface**: N/A
- **Verify**: `uv run pyright src/` limpo; `uv run pytest tests/test_forwardings.py` passa (após Steps 4+6)
- **Tests**: Coberto pelos testes de API do Step 6
- [ ] Done

---

### Step 3: Use case `ListForwardingsForAuthor`

Criar `src/fala_gavea/application/use_cases/forwardings/list_forwardings_for_author.py`. O use case espelha `ListForwardingsForReport` mas recebe `author_id: str` (sem validação de existência — o autor é o próprio usuário autenticado, validado na camada de apresentação). Retorna `list[tuple[Forwarding, list[Report]]]` hidratando os relatos de cada encaminhamento.

```python
class ListForwardingsForAuthor:
    def __init__(self, forwarding_repo, report_repo): ...
    def execute(self, author_id: str) -> list[tuple[Forwarding, list[Report]]]:
        forwardings = self._forwarding_repo.find_by_author_id(author_id)
        result = []
        for fwd in forwardings:
            report_ids = self._forwarding_repo.get_report_ids(fwd.id)
            reports = [r for rid in report_ids if (r := self._report_repo.find_by_id(rid)) is not None]
            result.append((fwd, reports))
        return result
```

- **Files**: `src/fala_gavea/application/use_cases/forwardings/list_forwardings_for_author.py` (create)
- **References**: `src/fala_gavea/application/use_cases/forwardings/list_forwardings_for_report.py` (padrão a espelhar)
- **Depends on**: Step 1
- **Interface**: `ListForwardingsForAuthor(forwarding_repo, report_repo).execute(author_id: str) -> list[tuple[Forwarding, list[Report]]]`
- **Verify**: `uv run pyright src/` limpo
- **Tests**: Coberto pelos testes de API do Step 6
- [ ] Done

---

### Step 4: Rota `GET /forwardings/mine` no router

Adicionar o endpoint `GET /forwardings/mine` em `src/fala_gavea/presentation/api/routers/forwardings.py`. A rota deve ser registrada **antes** do `GET /{id}` para evitar que FastAPI interprete "mine" como um parâmetro de path (mesma razão do `/public`). Usar `get_current_user` (não `require_any_role`) — cidadão, agente e admin têm acesso. Retornar `list[PublicForwardingResponse]` (sem `agent_id`).

```python
from fala_gavea.presentation.api.dependencies import get_current_user  # já importado via _agent_or_admin chain

@router.get("/mine", response_model=list[PublicForwardingResponse])
def list_my_forwardings(
    current_user: User = Depends(get_current_user),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
) -> list[PublicForwardingResponse]:
    pairs = ListForwardingsForAuthor(forwarding_repo, report_repo).execute(current_user.id)
    return [_build_public_response(fwd, reports) for fwd, reports in pairs]
```

Importar `ListForwardingsForAuthor` e verificar se `get_current_user` já está importado (atualmente só `require_any_role` e `get_forwarding_repo`/`get_report_repo` são importados; `get_current_user` pode precisar ser adicionado).

- **Files**: `src/fala_gavea/presentation/api/routers/forwardings.py` (modify)
- **References**: `product-design/project/product-design-as-coded.md § 4` (modelo de permissão)
- **Depends on**: Step 3
- **Interface**: N/A
- **Verify**: `curl -H "Authorization: Bearer <citizen_token>" /forwardings/mine` → 200 com lista (incluindo vazia); sem auth → 401
- **Tests**: Step 6
- **Docs**: Atualizar as-coded após merge (via post-skill)
- [ ] Done

---

### Step 5: Frontend — hook e toggle "Meus encaminhamentos"

Três mudanças no frontend:

**a) `frontend/src/lib/api.ts`** — adicionar método `getMyForwardings()`:
```ts
getMyForwardings(): Promise<PublicForwarding[]> {
  return request<PublicForwarding[]>("GET", "/forwardings/mine");
}
```
Este método não passa `{ public: true }` — usa o token do `localStorage` normalmente.

**b) `frontend/src/hooks/useForwardings.ts`** — adicionar hook:
```ts
export function useMyForwardings() {
  return useQuery({
    queryKey: ["forwardings", "mine"],
    queryFn: () => api.getMyForwardings(),
    staleTime: 30_000,
  });
}
```

**c) `frontend/src/features/forwardings/PublicForwardingsPage.tsx`** — adicionar toggle "Meus encaminhamentos":
- Importar `useAuth` e `useMyForwardings`
- Adicionar estado `showMine: boolean` (default false)
- Quando `showMine && user` → usar dados de `useMyForwardings()`; caso contrário → dados existentes de `usePublicForwardings()`
- Toggle (checkbox ou switch) visível somente quando `user` não é null

- **Files**:
  - `frontend/src/lib/api.ts` (modify)
  - `frontend/src/hooks/useForwardings.ts` (modify)
  - `frontend/src/features/forwardings/PublicForwardingsPage.tsx` (modify)
- **References**: `product-design/project/standards.md § Frontend`
- **Depends on**: Step 4
- **Interface**: N/A
- **Verify**: Cidadão logado vê toggle; ao ativar, lista filtra para encaminhamentos dos seus relatos; usuário não logado não vê toggle
- **Tests**: N/A (testes de UI são manuais neste projeto; lógica de dados coberta pelos testes de API)
- [ ] Done

---

### Step 6: Testes para `GET /forwardings/mine`

Adicionar 3 casos de teste em `tests/test_forwardings.py` usando as fixtures existentes (`client`, `citizen_headers`, `agent_headers`, `sample_report_type`):

**Caso 1 — happy path:** cidadão cria 2 relatos, agente cria forwarding com ambos; `GET /forwardings/mine` com `citizen_headers` retorna 200 com lista contendo o forwarding.

**Caso 2 — exclusão correta:** cidadão2 cria relatos, agente cria forwarding com relatos de cidadão2; `GET /forwardings/mine` com `citizen_headers` (cidadão1) retorna lista vazia (precisa de fixture para cidadão2 ou criar usuário inline).

**Caso 3 — 401 sem auth:** `GET /forwardings/mine` sem headers retorna 401.

```python
def test_mine_returns_forwarding_with_own_reports(client, citizen_headers, agent_headers, sample_report_type):
    r1 = _create_report(client, citizen_headers, sample_report_type)
    _create_forwarding(client, agent_headers, [r1["id"]])
    resp = client.get("/forwardings/mine", headers=citizen_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_mine_excludes_forwardings_of_other_citizens(client, citizen_headers, agent_headers, sample_report_type, db_session):
    # criar outro cidadão diretamente no DB e seus relatos
    ...
    resp = client.get("/forwardings/mine", headers=citizen_headers)
    assert resp.status_code == 200
    assert resp.json() == []

def test_mine_requires_auth(client):
    resp = client.get("/forwardings/mine")
    assert resp.status_code == 401
```

- **Files**: `tests/test_forwardings.py` (modify)
- **References**: `product-design/project/standards.md § Testing`
- **Depends on**: Step 4
- **Interface**: N/A
- **Verify**: `uv run pytest tests/test_forwardings.py -v` passa com os 3 novos casos
- **Tests**: N/A (este step É os testes)
- [ ] Done

---

## Commit Message

```
feat(forwardings): add GET /forwardings/mine for authenticated citizens

Citizens can now list all forwardings that contain at least one of their
own reports via GET /forwardings/mine (auth-required, any role).

Returns PublicForwardingResponse (no agent_id). Implemented via new
find_by_author_id repo method (DISTINCT JOIN through forwarding_reports
→ reports) + ListForwardingsForAuthor use case + frontend toggle
"Meus encaminhamentos" in PublicForwardingsPage.

Resolves research-000168 Option C recommendation.
```

## As-Coded Delta

```
GET /forwardings/mine (any authenticated user) — returns PublicForwardingResponse list of forwardings
containing at least one report authored by the current user. Backed by new find_by_author_id
repo method (DISTINCT JOIN forwarding_reports → reports) and ListForwardingsForAuthor use case.
Frontend: useMyForwardings hook + "Meus encaminhamentos" toggle in PublicForwardingsPage.
```
