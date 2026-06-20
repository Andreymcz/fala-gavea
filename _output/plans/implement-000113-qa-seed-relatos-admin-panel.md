# Implement 000113 QA | 2026-06-20 22:58 UTC | Seed de Relatos no painel admin (CSV enriquecido)

**Brief:** implement 113

## Q&A log

**Q: O que o plano 000113 implementa?**
A: Enriquece o seed de relatos e expõe uma seção "Seed de Relatos" no painel admin. Backend: `BulkCreateReports` passa a resolver autor por `user_id` (auto-cria/deduplica conta de cidadão por e-mail sintético), auto-cria tópico inexistente (com guarda contra nomes <3 chars), e aplica fallbacks (coordenada aleatória na Gávea, data=now, urgency=media). Endpoint `POST /admin/seed/relatos` lê as colunas novas (`user_id`, `urgency`; alias `id_cidadao`) e injeta `user_repo`/`password_service`. Frontend: `api.seedRelatos(file)` + card com regras pt-BR em `AdminPage.tsx`.

**Q: Modo de execução?**
A: Manual (4 steps, dependências lineares), executado in-context.

**Q: Houve mudança de assinatura com impacto?**
A: Sim — `BulkCreateReports.execute` trocou `author_id` por `user_repo` + `password_service`. Único chamador é `seed.py`, atualizado no mesmo plano. `test_bulk_create_reports.py` foi reescrito (13 testes) e `test_seed_endpoint.py` atualizado (5 testes) por codificarem o comportamento antigo.

**Q: Resultado do Quality Gate?**
A: ruff/pyright limpos nos arquivos alterados; pytest 116 passed + 2 falhas pré-existentes não relacionadas (`test_report_types.py`: `POST /report_types/` permite citizen/não-autenticado — bug pré-existente confirmado em HEAD limpo); frontend 32 passed.

**Q: Itens de atenção?**
A: (1) Bug pré-existente de autorização em `POST /report_types/` — recomendado `/plan` para corrigir. (2) Contas auto-criadas usam senha padrão `changeme` — aceitável apenas em dev (confirmado no plano).
