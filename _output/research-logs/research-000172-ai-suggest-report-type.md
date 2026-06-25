# Research 000172 | FEATURE-X | 2026-06-25 19:35 | AI-assisted report_type suggestion
tags: ai-suggestion, report-type, chromadb, agent-workflow, data-model

## User Brief

AI-assisted report_type suggestion: map the full design space — nullable report_type_id migration, SuggestReportTypeUseCase via ChromaDB similarity, PATCH /reports/{id}/report-type for agent/admin, ai_source provenance field, and UX for suggestion review.

Clarificacao durante a sessao: "topico" = `report_type` (tipo de relato). O campo ja existe. "precisamos de uma ferramenta de agente/admin para editar um topico de um relato."

## Agent Interpretation

Mapear o design completo para introduzir sugestao de `report_type` assistida por IA:
1. Permitir relatos sem tipo (nullable ou sentinel)
2. Proveniencia do tipo (citizen / ai_suggested / agent_override)
3. Mecanismo de sugestao via similaridade semantica (ChromaDB)
4. Endpoint PATCH para agente/admin confirmar ou substituir sugestao
5. Fila de revisao de sugestoes na UX do agente

## Files

- `src/fala_gavea/domain/entities/report.py` — entidade Report; `report_type_id: str` obrigatorio
- `src/fala_gavea/infrastructure/database/models.py` — `ReportModel`; `nullable=False` no FK
- `src/fala_gavea/infrastructure/repositories/sqlalchemy_report_repository.py` — `save()` nao atualiza `report_type_id` (bug)
- `src/fala_gavea/infrastructure/chromadb/chroma_search_client.py` — cliente ChromaDB; indexa `report_type_id` nos metadados
- `src/fala_gavea/presentation/api/routers/reports.py` — router atual; sem endpoint PATCH
- `src/fala_gavea/domain/repositories/semantic_ports.py` — portas semanticas; precisam de extensao

---

## Q&A Log

**Q1:** Como introduzir no codebase a opcao da IA sugerir topicos para relatos com topicos inexistentes, com minima friccao?

**A1:**

### Descoberta 1 — Bug critico em `save()` [BLOQUEADOR]

`SQLAlchemyReportRepository.save()` atualiza `text, lat, lon, urgency, photo_url, status` no branch de update, mas **nao atualiza `report_type_id`**. Qualquer PATCH que chame `save()` com um novo `report_type_id` sera silenciosamente descartado. Este bug deve ser corrigido no mesmo plano que o endpoint PATCH.

### Descoberta 2 — `report_type_id NOT NULL` e o problema de migracao

O campo e `nullable=False` no modelo SQLAlchemy e no banco. O projeto usa `Base.metadata.create_all()` — que **nunca executa ALTER TABLE** em bancos existentes. Mudar para `nullable=True` no modelo nao altera o banco em producao: e um no-op silencioso.

**Opcoes:**

| Opcao | Risco | Complexidade | Recomendacao |
|---|---|---|---|
| **Sentinel "Nao classificado"** | Baixo — sem schema change | Baixa | **Preferida** |
| Nullable + raw ALTER TABLE script | Medio — SQLite requer table-rebuild | Media | Valida se quiserem NULL semantico |
| Introducao de Alembic | Baixo a longo prazo | Alta (setup inicial) | Para o futuro |

A abordagem sentinel usa um `ReportType` especial com `id="unknown"` / `name="Nao classificado"` seeded no banco. Relatos sem tipo recebem esse ID na criacao; o frontend nao exibe esse tipo nos filtros/listagens normais.

### Descoberta 3 — Arquitetura da sugestao (porta nova)

O `ChromaSearchClient` viola `CONVENTION_1` se acessado diretamente em use cases. A solucao correta:

```
domain/repositories/
  report_type_suggestion_port.py   # IReportTypeSuggestionPort(ABC)
      suggest(text: str, n: int) -> list[tuple[str, float]]

infrastructure/chromadb/
  chroma_report_type_client.py     # ChromaReportTypeClient
      — colecao separada: "falagavea_report_types"
      — indexa ReportType.name + ReportType.description
      — query = texto do relato; retorna (report_type_id, score)

application/use_cases/reports/
  suggest_report_type.py           # SuggestReportTypeUseCase
      — injeta IReportTypeSuggestionPort
      — retorna list[SuggestResult(report_type_id, name, score)]
```

O `SuggestReportTypeUseCase` nao importa ChromaDB.

### Descoberta 4 — Proveniencia

Campo `report_type_source` como enum nullable na tabela `reports`:

```python
class ReportTypeSource(str, Enum):
    citizen = "citizen"           # tipo definido pelo cidadao na criacao
    ai_suggested = "ai_suggested" # tipo sugerido pela IA, ainda nao confirmado
    agent_override = "agent_override"  # tipo confirmado/corrigido por agente/admin
```

`NULL` = registros legados (pre-feature). Sem tabela de auditoria neste momento.

Como e uma coluna nova, tambem requer migracao em bancos existentes (mesmo problema do nullable). A estrategia sentinel + `Base.metadata.create_all()` funciona apenas para bancos novos. Para bancos existentes: script de migracao manual ou introducao de Alembic.

**Recomendacao pratica para este projeto (fase academica):** aceitar que seeds e testes usam banco zerado; `create_all()` aplica o novo schema. Documentar que producao precisaria de script de migracao.

### Descoberta 5 — Endpoint PATCH

`PATCH /reports/{id}/report-type` e a granularidade correta:
- Restricao explicita: agentes nao podem alterar texto, localizacao, urgencia por esta rota
- Role guard: `require_any_role("agent", "admin")` ja existe
- Politica de autorizacao: qualquer agente pode sobrescrever o tipo de qualquer relato (nao ha scoping por distrito/cessao neste sistema). Esta politica deve ser explicitada no codigo.
- Body: `{"report_type_id": "...", "source": "agent_override"}`

### Descoberta 6 — Re-indexacao ChromaDB

O `ChromaSearchClient.index()` armazena `report_type_id` nos metadados. Apos override, o use case deve:
1. Chamar `indexer.delete(report_id)`
2. Chamar `indexer.index(updated_report)`

Isso evita que buscas semanticas filtradas por tipo retornem metadados desatualizados.

### Descoberta 7 — UX da fila de revisao

O agente precisa de:
1. **Fonte de dados**: filtro `awaiting_type_review=true` no endpoint `/reports/query` existente (novo campo booleano em `ReportQueryRequest`) — retorna relatos com `report_type_source="ai_suggested"` ou tipo sentinel
2. **Confianca visivel**: `SuggestReportTypeUseCase` retorna `score: float` (0-1) — UI exibe; threshold sugerido: 0.65
3. **Acoes**: Confirmar (aplica `agent_override`) / Substituir (escolhe outro tipo) / Deixar pendente

### Resumo de dependencias entre os componentes

```
[seed "Nao classificado" ReportType]
       ↓
[ReportCreate: report_type_id opcional; usa sentinel se ausente]
       ↓
[SuggestReportTypeUseCase: ChromaDB similarity → sugere tipo + score]
       ↓
[PATCH /reports/{id}/report-type: agente confirma/substitui]
       ↓
[save() corrigido: persiste report_type_id + report_type_source]
       ↓
[ChromaDB re-index: metadados atualizados]
```

---

## Recommendations Summary

| # | Prioridade | Recomendacao |
|---|---|---|
| R1 | **ALTA** | Adotar sentinel `ReportType` id=`"unknown"` / name=`"Nao classificado"` em vez de nullable. Evita migracao de schema para bancos existentes; compativel com `create_all()`. |
| R2 | **ALTA** | Corrigir `save()` em `sqlalchemy_report_repository.py` para incluir `report_type_id` e `report_type_source` no branch de update. |
| R3 | **ALTA** | Definir `IReportTypeSuggestionPort` em `domain/repositories/` e implementar `ChromaReportTypeClient` em `infrastructure/chromadb/`. Manter `SuggestReportTypeUseCase` sem importacoes de ChromaDB. |
| R4 | **ALTA** | Adicionar coluna `report_type_source` (enum nullable) ao modelo `ReportModel` e entidade `Report`. Para fase academica: aceitar banco zerado; documentar necessidade de migracao em producao. |
| R5 | **MEDIA** | Implementar `PATCH /reports/{id}/report-type` com `require_any_role("agent", "admin")` e documentar explicitamente a politica de acesso irrestrito. |
| R6 | **MEDIA** | Adicionar filtro `awaiting_type_review: bool` ao `ReportQueryRequest` para servir a fila de revisao do agente. |
| R7 | **MEDIA** | Retornar `confidence: float` do `SuggestReportTypeUseCase`; definir threshold de 0.65 como constante configuravel. Sugestao ocorre de forma sincrona na criacao se `report_type_id` ausente. |
| R8 | **MEDIA** | Re-indexar ChromaDB (delete + index) dentro do use case de PATCH para manter metadados de `report_type_id` atualizados. |
| R9 | **BAIXA** | Documentar caminho de upgrade para Alembic quando o projeto precisar de migracoes em producao. |

---

## Trade-offs Registrados

**Sentinel vs. Nullable:** Sentinel e mais pragmatico para esta fase (sem schema change), mas introduz um valor magico que deve ser filtrado na listagem de tipos para cidadaos. Nullable e semanticamente correto mas requer table-rebuild no SQLite.

**PATCH estreito vs. PATCH geral:** `PATCH /reports/{id}/report-type` e mais seguro e expressivo; `PATCH /reports/{id}` seria mais REST-puro mas exigiria enforcement de permissoes por campo. O estreito e a escolha certa aqui.

**Sugestao sincrona vs. background:** Sincrona e mais simples e adequada para o volume atual (ChromaDB local, ~200-5k relatos). Background task seria overkill.
