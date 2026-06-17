# PROJECT CONSTITUTION — fala-gavea

fala-gavea — Sistema de demandas de cidadaos para seguranca urbana na Gavea. Cidadao registra problema (localizacao, tipo, urgencia); agente publico cria encaminhamento para orgao competente; IA assiste exploracao por busca semantica e chat NL.

Designed for the INF2921/CIS2114 AI Systems Design course (2026.1, PUC-Rio). Team: Andrey, Mauro, Julia, Herbert, Natali.

---

## Technical Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| T1 | Todas as chamadas LLM e buscas semanticas passam pelo `infrastructure/` (ChromaClient, OllamaClient) — nenhum acesso direto a ChromaDB ou Ollama em use cases ou routers | Centraliza configuracao de modelo e torna substituicao uma mudanca de uma linha |
| T2 | Autenticacao e middleware — nenhum router acessa JWT diretamente; use `dependencies.py` (get_current_user, require_role) | Mantém um único caminho auditavel de autenticacao; previne deriva de esquema de auth |
| T3 | Type annotations obrigatorias em todas as funcoes publicas; configuracao via env vars (FALA_GAVEA_OLLAMA_URL, FALA_GAVEA_OLLAMA_MODEL, DATABASE_URL) | Habilita verificacao pyright; garante portabilidade de ambiente sem mudancas de codigo |
| T4 | `gavealab.db` e gitignored — nunca commitado | Dados de cidadaos e resultados de analise sao artefatos privados derivados, nao arquivos-fonte |
| T5 | Todo acesso a banco de dados vai atraves de repositorios em `infrastructure/repositories/` — use cases nunca acessam SQLAlchemy diretamente | Mantem camada de dominio pura e testavel sem banco de dados |

---

## Quality Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| Q1 | Todos os testes usam pytest — sem scripts ad-hoc como substitutos | Descoberta consistente e relatorio de cobertura via `uv run pytest` |
| Q2 | Ruff linting passa antes de qualquer commit (`uv run ruff check src/ tests/`) | Mantem estilo de codigo consistente entre a equipe |
| Q3 | Type annotations obrigatorias em todas as funcoes publicas em `src/fala_gavea/` | Captura erros de tipo antecipadamente |

---

## Security Invariants

| # | Invariant | Rationale |
|---|-----------|-----------|
| S1 | Nenhuma API key ou credencial no codigo-fonte — todos os secrets vem de variaveis de ambiente | Previne vazamento de credenciais no historico git |
| S2 | `fala_gavea.db` e gitignored — dados de cidadaos nunca commitados | Previne exposicao acidental de dados sensiveis |
| S3 | Busca semantica e LLM sao somente-leitura em relacao ao banco — apenas endpoints REST escrevem dados | Limita impacto de qualquer uso indevido do MCP a recuperacao |

---

## Compliance Requirements

| # | Requirement | Rationale |
|---|-------------|-----------|
| C1 | Dados de cidadaos nunca saem da maquina local — toda inferencia LLM via Ollama local | Principio de privacidade primeiro — soberania de dados para o pesquisador |

---

## Enforcement

- Estas principios sao carregados em todo contexto de agente via pre-skill.
- `/check validate` verifica conformidade.
- Violacoes descobertas durante `/check review` sao classificadas como **blocking**.

---

## Changelog

### v1 — 2026-06-17
- Constituicao inicial criada via `/seja-setup` (plan-000072 step 3).
