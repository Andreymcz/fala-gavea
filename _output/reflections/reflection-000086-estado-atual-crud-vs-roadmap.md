# Reflection 000086 | 2026-06-18 19:38 UTC | estado atual crud vs roadmap

## Artifacts reflected on

- [roadmap-00001-gavea-seguranca-demandas-app.md](../roadmaps/roadmap-00001-gavea-seguranca-demandas-app.md)
- [product-design-as-coded.md](../../product-design/project/product-design-as-coded.md)
- [plan-000073-feature-b-wave-0-item-1-domain-auth-reports.md](../plans/plan-000073-feature-b-wave-0-item-1-domain-auth-reports.md)
- [plan-000075-feature-b-wave-0-item-2-report-type-crud.md](../plans/plan-000075-feature-b-wave-0-item-2-report-type-crud.md)
- [plan-000079-feature-b-wave-1-item-3-forwarding-crud.md](../plans/plan-000079-feature-b-wave-1-item-3-forwarding-crud.md)
- [plan-000082-feature-f-wave-1-item-4-frontend-spa-react.md](../plans/plan-000082-feature-f-wave-1-item-4-frontend-spa-react.md)
- [plan-000085-qa-seed-relatos-1-ano.md](../plans/plan-000085-qa-seed-relatos-1-ano.md)

## Summary

O roadmap-000071 definiu 3 waves. Wave 0 (scaffold + dominio + ReportType CRUD) e Wave 1
(Forwarding CRUD + Frontend SPA React) foram concluidas integralmente nos ultimos 2 dias.
Wave 2 (IA: busca semantica, relatos similares, chat NL) permanece pendente — nenhum dos
3 itens foi iniciado.

**Inventario CRUD implementado (14 endpoints live):**

| Entidade | C | R (list) | R (detail) | U | D |
|----------|---|----------|------------|---|---|
| User | POST /auth/register | — | — | — | — |
| Report | POST /reports | GET /reports/geojson | GET /reports/{id} | ❌ | ❌ |
| ReportType | POST /report_types | GET /report_types | — | PATCH /{id} | DELETE /{id} soft |
| Forwarding | POST /forwardings | GET /forwardings | GET /forwardings/{id} | PATCH /{id} + /{id}/status | ❌ |

Lacunas no CRUD atual:
- Report nao tem PATCH nem DELETE; listagem disponivel apenas em formato GeoJSON
- User nao tem perfil nem painel admin (§9 as-coded: "Not yet implemented")
- Forwarding nao tem DELETE
- Wave 2 inteira (IA) pendente

Seeds disponiveis: 8 tipos de relato, 3 usuarios dev, 10k relatos com spread de 1 ano.

Jornadas JM-TB-001 (cidadao registra relato) e JM-TB-002 (agente cria encaminhamento)
estao implementadas end-to-end (backend + SPA frontend).

## Reflection

Precisamos refinar as jornadas das personas

## Follow-ups

- Quais passos das jornadas JM-TB-001 e JM-TB-002 precisam de refinamento? Lacunas de UX,
  fluxos ausentes, ou divergencias entre o que foi projetado e o que foi implementado?
- A persona Administrador (R-P-003) nao tem jornada implementada (admin panel §9 ausente)
  -- isso e um gap intencional ou precisa entrar no roadmap?
- O CRUD de Report sem PATCH/DELETE e uma lacuna de design (cidadao nao edita/cancela
  demandas?) ou uma decisao explicita do PoC?
- Wave 2 depende de ChromaDB + Ollama locais -- ha prerequisitos de ambiente a verificar
  antes de iniciar o plano?
