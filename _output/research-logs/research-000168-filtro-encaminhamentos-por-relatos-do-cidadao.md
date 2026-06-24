# Research 000168 | fala-gavea | 2026-06-24 19:43 UTC | Filtro de encaminhamentos por relatos do cidadão

tags: citizen-access, forwardings, api-design, security, architecture
spawned: plan-000169

## User Brief

"como cidadao logado, como posso acessar os encaminhamentos que possuem relatos meus ???? acho que temos que criar um filtro para encaminhamentos"

## Agent Interpretation

Investiga como um cidadão autenticado pode consultar todos os encaminhamentos que contêm pelo menos um de seus relatos. A pergunta inclui uma hipótese (criar um filtro para encaminhamentos) que foi avaliada em comparação com abordagens alternativas.

## Files Consulted

- `src/fala_gavea/presentation/api/routers/forwardings.py`
- `src/fala_gavea/domain/repositories/forwarding_repository.py`
- `src/fala_gavea/presentation/api/routers/reports.py` (trecho `/{id}/forwardings`)
- `frontend/src/features/forwardings/PublicForwardingsPage.tsx`
- `frontend/src/features/forwardings/PublicForwardingRow.tsx`
- `frontend/src/hooks/useForwardings.ts`
- `frontend/src/lib/api.ts`
- `product-design/project/product-design-as-coded.md`

---

## Q&A Log

### Q1

**Pergunta:** Como cidadão logado posso acessar os encaminhamentos que possuem relatos meus? Precisamos de um filtro para encaminhamentos?

**Resposta:**

#### Estado atual

O sistema tem as seguintes rotas de encaminhamento:

| Endpoint | Acesso | Filtros disponíveis |
|---|---|---|
| `GET /forwardings/public` | Público (sem auth) | `status` apenas |
| `GET /forwardings/public/{id}` | Público | — |
| `GET /reports/{id}/forwardings` | Público | por relato específico |
| `GET /forwardings` | agent+admin | status, institution, agent_id, since, until |

**Gap identificado:** Não existe endpoint para "os encaminhamentos que contêm pelo menos um relato meu" — o cidadão autenticado não tem esse caminho direto.

#### Opções avaliadas

**Opção A — Agregação no frontend (sem mudança de backend)**
- Frontend busca os relatos do cidadão, chama `GET /reports/{id}/forwardings` para cada um, deduplica.
- Problema: O(N) requisições; lento para cidadãos com muitos relatos (seed tem 5k relatos).

**Opção B — Adicionar `author_id` ao `GET /forwardings/public`**
- Adiciona `?author_id=<uuid>` como query param público.
- **Rejeitada por segurança:** qualquer chamador que conhece o UUID do cidadão pode espionar o histórico de encaminhamentos sem autenticação. O UUID também fica exposto em logs de acesso, histórico do browser e proxies HTTP — risco de PII em URL pública.

**Opção C — Novo `GET /forwardings/mine` (auth-required) ✅ RECOMENDADA**
- Endpoint autenticado que usa `current_user.id` como filtro interno.
- Query: `SELECT DISTINCT f.* FROM forwardings f JOIN forwarding_reports fr ON fr.forwarding_id = f.id JOIN reports r ON r.id = fr.report_id WHERE r.author_id = :current_user_id`
- Retorna `list[PublicForwardingResponse]` (sem `agent_id` — cidadão não precisa ver isso).
- Pros: auth protege o acesso; nenhum UUID vaza na URL; semântica limpa.

**Opção D — `mine=true` no endpoint público (auth-opcional)**
- Complica um endpoint "público" com lógica de auth — anti-padrão; rejeitada.

#### Recomendação

Implementar **Opção C**: `GET /forwardings/mine` auth-required.

**Mudanças necessárias (4 arquivos, 1 novo):**

1. **`src/fala_gavea/domain/repositories/forwarding_repository.py`**
   - Adicionar método abstrato `find_by_author_id(author_id: str) -> list[Forwarding]`
   - **Não alterar** `ForwardingFilters` — este dataclass pertence à superfície agent/admin

2. **`src/fala_gavea/infrastructure/repositories/sqlalchemy_forwarding_repository.py`**
   - Implementar `find_by_author_id` com JOIN: `forwardings → forwarding_reports → reports WHERE reports.author_id = author_id`

3. **`src/fala_gavea/application/use_cases/forwardings/list_forwardings_for_author.py`** *(novo)*
   - Use case análogo ao existente `list_forwardings_for_report.py`

4. **`src/fala_gavea/presentation/api/routers/forwardings.py`**
   - Adicionar rota `GET /mine` **antes** de `GET /{id}` (mesma regra de ordenação do `/public`)
   - Usar `get_current_user` (não `require_any_role`) — todos os papéis, inclusive cidadão, têm acesso

5. **Frontend (opcional mas recomendado)**
   - Adicionar hook `useMyForwardings()` em `hooks/useForwardings.ts`
   - Adicionar toggle "Meus encaminhamentos" na `PublicForwardingsPage` (visível só para usuários autenticados)

---

## Recommendations Summary

| # | Prioridade | Recomendação |
|---|---|---|
| 1 | **HIGH** | Implementar `GET /forwardings/mine` (auth-required) com `get_current_user`, retornando `list[PublicForwardingResponse]` |
| 2 | **HIGH** | Rejeitar Opções B e D — risco de privacidade (author_id em URL pública); não negociável |
| 3 | **MEDIUM** | Não usar Opção A como fallback — O(N) requisições é UX inaceitável para seed de 5k relatos |
| 4 | **MEDIUM** | Não adicionar `author_id` a `ForwardingFilters` — o dataclass pertence à superfície agent/admin |
| 5 | **LOW** | Endereçar em follow-up o N+1 pré-existente nas listagens de encaminhamentos (`list_public_forwardings` chama `GetForwarding` por item) |
