# Plan 000113 QA | Seed de Relatos no painel admin (design Q&A)

**Brief:** Seed de Relatos no painel admin com CSV enriquecido (user_id obrigatorio, auto-cria usuario/topico, fallbacks de coordenada/data/urgencia)

## Q&A log

**Q (usuário):** A seção "Seed de Tópicos" precisa receber um CSV com mais dados (ver `seed_relatos.py`): coluna `user_id` obrigatória, criar conta com senha padrão `<changeme>` se não existir; popular o banco de forma mais completa em relação ao modelo. "Ver se posso ter esquecido de algo."

**A:** Esclarecido que o pedido é sobre **seed de relatos** (reports), não tópicos (report types) — `user_id` não cabe em tópicos. O endpoint `POST /admin/seed/relatos` já existe mas (a) usa o admin logado como autor de todos os relatos e (b) fixa `urgency=media`, e nenhuma UI o expõe. Levantadas lacunas vs. o modelo: autoria por linha, urgency/status/photo_url ignorados, forwardings não semeados, idempotência, tópico ausente.

### Decisões (AskUserQuestion)

- **Autor / user_id:** `user_id` **sintetiza e-mail/nome** → e-mail `{user_id}@seed.gavea.br`, name `Cidadão {user_id}`, role `citizen`. (Descartadas: coluna `email` direta; UUID existente com falha.)
- **Cobertura do "popular mais completo":** apenas **urgency por linha**. (Fora: status variado, photo_url, encaminhamentos.)
- **Exposição:** **nova seção "Seed de Relatos" no painel admin** (upload CSV), espelhando a de Tópicos. (Não: só backend/script.)

### Confirmações adicionais

- **Senha padrão:** string literal `changeme` (não `<changeme>`); confirmado ambiente de **dev**.
- **Idempotência:** OK duplicar relatos em re-run (sem proteção no endpoint); só usuários são deduplicados por e-mail.

### Regras de fallback adicionadas pelo usuário

- Tópico inexistente → **criar** (auto-cria o ReportType).
- Sem latitude/longitude → coordenada **aleatória no escopo da Gávea**.
- Sem data → **data do momento da criação** no banco.
- Essas regras devem aparecer em **pt-BR na UI** para o usuário.

## Achados da revisão (plan-reviewer, standard)

- **F-TEST (High):** `tests/test_bulk_create_reports.py` (10 testes) quebra na nova assinatura; 2 testes codificam comportamento agora inválido → plano reescreve o arquivo.
- **F1 (High):** auto-criar tópico via `CreateReportType` lança `InvalidInputError` para nomes <3 chars → guarda com try/except para não abortar o batch.
- **F2 (Medium):** usar o retorno de `CreateReportType.execute` em vez de re-fetch.
- **F4 (Low/Med):** manter índice de erro **base-0** (contrato atual), não base-1.
- **F5 (Low):** documentar que reuso de conta nunca regrava a senha de usuário existente.
