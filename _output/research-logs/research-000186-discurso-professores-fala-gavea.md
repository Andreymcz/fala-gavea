# Research 000186 | fala-gavea | 2026-06-28 12:44 UTC | Discurso para professores: o que foi implementado
tags: communication, architecture, journeys, semantic-search, llm

## User brief

> eu quero comunicar para os professores o que foi implementado no fala-gavea. seria interessante um discurso do problema -> casos de uso -> jornadas -> features do sistema. Arquitetura do software -> stack tecnológico suportantdo as features (db, chroma, llm)

## Agent interpretation

O usuário quer um **discurso/roteiro de apresentação** para professores (audiência acadêmica, INF2921 — AI Systems Design), narrando o que de fato foi implementado no fala-gavea, seguindo um arco: **problema → casos de uso → jornadas → features → arquitetura → stack tecnológico** (com ênfase em como DB, ChromaDB e LLM sustentam as features.

Isto é uma tarefa de **estruturação de comunicação ancorada na realidade do código** — não uma decisão de design. Por isso, como precedente no research-000185, o passo de revisão multi-perspectiva não se aplica; o material é fundamentado direto no `product-design-as-coded.md`, nas jornadas/casos de uso projetados e no `src/`.

**Princípio honesto (herdado de research-000185):** o discurso separa o **entregue** do **idealizado/trabalho futuro**. O ponto crítico é a *IA como auxiliar* — busca semântica, similares, RAG, NL→filtro, palavras-chave TF-IDF **existem**; já **sugestão de categorização por IA, correção como evento de curadoria e loop de few-shot NÃO existem** (são hipótese de design). Não os apresente como entregues.

## Files inspected

- `product-design/project/product-design-as-coded.md` (estado as-coded completo)
- `product-design/project/product-design-as-intended.md` §13 (casos de uso US-001..003), §15 (jornadas JM-TB-001..003), Decisions D-001..D-017
- `product-design/project/ux-research-results.md` (personas R-P-001..003, cenários R-PS-001/002)
- `_output/research-logs/research-000185-fase5-text-vs-implementation-gap.md` (auditoria entregue vs idealizado)
- `CLAUDE.md` (stack), `product-design/conventions.md` (variáveis de arquitetura)

---

## O DISCURSO (roteiro de apresentação)

> Estrutura sugerida: 1 slide por seção numerada. Tempo-alvo ~10–12 min. Texto em pt-BR pronto para falar; rótulos `[fala]` são o que dizer, `[mostre]` é o artefato a exibir.

### 1. O Problema

[fala] *A segurança urbana na Gávea depende de um fluxo que hoje está quebrado nas duas pontas.*

- **Do lado do cidadão (R-P-001):** vê um problema — poste apagado, buraco, lixo — e **não tem um canal claro**. Tenta o 1746 e fica em espera; pesquisa no Google e cai no órgão errado; manda no WhatsApp da associação e ninguém responde. Desiste, e o problema persiste por semanas (cenário R-PS-001). A frustração central: *"reportei e nunca soube o que aconteceu"*.
- **Do lado do agente público (R-P-002):** recebe demandas de múltiplos canais (telefone, e-mail, WhatsApp, 1746) e tria **uma lista de texto, sem mapa, sem agrupamento**. Três relatos do mesmo poste — "luz apagada", "poste sem luz", "rua escura" — viram **três encaminhamentos** para a RioLuz, que manda três equipes ao mesmo lugar (cenário R-PS-002). A triagem manual consome ~45 min e duplica trabalho.

[fala] *O problema, então, é duplo: o cidadão não tem onde registrar com transparência, e o agente não tem como explorar e agrupar demandas similares de forma eficiente. fala-gavea fecha esse laço cidadão → agente → cidadão numa única solução.*

### 2. Casos de Uso

[fala] *Três casos de uso ancoram o sistema (User Stories §13):*

- **US-001 — Cidadão registra um relato georreferenciado.** "Como cidadão, quero registrar um problema (ex.: poste apagado) para que o poder público tome ciência." Critérios: login → formulário (tipo, urgência, texto, GPS automático) → relato aparece no mapa público com status `pendente`.
- **US-002 — Agente cria encaminhamento institucional.** "Como agente, quero selecionar relatos de postes apagados e encaminhar formalmente à RioLuz." Critérios: filtra por tipo → seleciona múltiplos relatos → informa instituição + solução proposta → relatos passam a `encaminhado`; encaminhamento nasce `aguardando_solucao`.
- **US-003 — Agente explora por busca semântica.** "Como agente, quero buscar por conteúdo em linguagem natural para achar padrões antes de encaminhar." Critérios: busca textual livre → resultados/similares → chat NL que **cita os IDs dos relatos** usados como contexto.

### 3. Jornadas

[fala] *Cada caso de uso virou uma jornada projetada — e todas as três estão implementadas ponta a ponta (frontend + backend).*

- **JM-TB-001 (Cidadão registra):** acessa formulário → escolhe tipo/urgência → descreve → "Usar minha localização" (geolocalização, com fallback de lat/lon editável) → opcional photo_url → "Registrar" → toast + redirect para o mapa com o novo marcador.
- **JM-TB-002 (Agente encaminha):** abre o workspace → filtra → (opcional) usa busca semântica/chat → seleciona relatos → "Cesta de relatos" → preenche instituição + solução → confirma → relatos viram `encaminhado` e o encaminhamento aparece no painel do agente.
- **JM-TB-003 (Explorar/analisar):** o workspace com filtro à esquerda e **visões intercambiáveis** ao centro: Mapa, Tabela, Palavras-chave, Similares, Chat, Cesta. Defaults por papel — cidadão vê Mapa+Tabela (transparência); agente/admin vê as visões analíticas. A IA aparece como **mais uma lente**, sempre citando de onde tirou a resposta.

[fala] *Note o gesto de design: o humano está no comando. A IA assiste, nunca decide.*

### 4. Features do Sistema

[fala] *O que está, de fato, no ar:*

**Cidadão / transparência**
- Registro de relato georreferenciado (tipo, urgência, texto, lat/lon, photo_url) — `POST /reports`.
- **Relato anônimo:** coordenadas arredondadas (3 casas) + token de reivindicação único; consulta posterior via `GET /reports/mine?anonymous_token=`.
- Mapa público clusterizado (react-leaflet-cluster) + exportação GeoJSON RFC 7946.
- **Transparência do encaminhamento sem login:** `GET /forwardings/public`, acompanhar um encaminhamento, ver encaminhamentos de um relato; "Meus relatos" e "Meus encaminhamentos" para o usuário autenticado.
- **Feedback cívico:** votos (up/down) e comentários em relatos e encaminhamentos.

**Agente / curadoria**
- Workspace em grid: filtro encenado (rascunho + "Aplicar"), chips de filtro ativo, presets de filtro salvos (`SavedFilter`).
- **Encaminhamento como agregação:** N relatos → 1 instituição, com solução proposta e ciclo de status (`aguardando_solucao → solucao_em_andamento → finalizado`).
- Endpoint unificado de consulta `POST /reports/query`: filtros multivalor + ranqueamento semântico + paginação.

**Camada de IA (assistência)**
- **Busca semântica** de relatos (`GET /reports/search`) e **similares** (`/reports/{id}/similar`, e por conjunto `POST /reports/similar-to-set`).
- **NL → filtro** (`POST /nl/filter`): o agente descreve a intenção em linguagem natural e o sistema propõe um filtro — **nunca auto-aplica** (o usuário clica "Aplicar sugestão ao rascunho").
- **Chat RAG** (`POST /nl/chat`): pergunta em linguagem natural sobre os relatos; a resposta **cita os IDs** dos relatos usados como contexto.
- **Palavras-chave** por TF-IDF + K-means (`GET /reports/keywords`).
- **Helper da plataforma** (`POST /nl/help`): um *segundo* chat RAG, sobre a própria documentação do projeto (como a plataforma funciona), com filtro de visibilidade por papel.
- **Marcador de proveniência de IA** (`AiBadge`) visível onde a IA atua.

**Admin**
- CRUD de tipos de problema (taxonomia dinâmica, não hardcoded; soft-delete).
- Bootstrap de admin via env vars; importação em lote de relatos/tópicos via CSV; wipe do banco (SQLite + ChromaDB).

[fala — escopo honesto] *Importante para uma plateia de IA: o que NÃO entregamos. Não há **sugestão de categoria por IA**, nem **edição de categoria pelo agente**, nem **evento de curadoria**, nem **loop de few-shot** que realimente a IA com as correções humanas. Isso foi pesquisado e planejado (plan-000174), mas permanece como **hipótese de design / trabalho futuro**. BERTopic está instalado, porém dormente. Apresentar isso como entregue seria impreciso.*

### 5. Arquitetura do Software

[fala] *Arquitetura limpa em quatro camadas, dependências apontando para dentro:*

```
presentation/   FastAPI routers, dependencies.py (get_current_user, require_role), schemas Pydantic
        ↓
application/     use cases — lógica de negócio pura, sem DB nem HTTP
        ↓
domain/          entidades (dataclasses puras) + interfaces de repositório/portas (ABCs)
        ↑
infrastructure/  SQLAlchemy repos, ChromaDB, LLM (Ollama/Anthropic), embeddings
```

Dois princípios de fronteira que vale destacar para professores:
- **Toda IA e busca semântica passa por `infrastructure/`** (ChromaSearchClient, Ollama/Anthropic) — nenhum use case ou router toca ChromaDB/LLM diretamente. As portas de domínio (`ISemanticSearchPort`, `IReportIndexer`, `ILLMClient`, `IDocSearchPort`) tornam a IA **plugável e testável**.
- **Autenticação centralizada:** nenhum router lê JWT direto; tudo via `dependencies.py`. Atribuição de autor sempre do token (`author_id = current_user.id`), nunca do corpo da requisição — previne falsificação.

[mostre] o diagrama de camadas acima + um exemplo de fluxo: `POST /reports` → `CreateReport` use case → `report_repo.save()` → hook opcional `indexer.index(report)` (falha de indexação loga WARNING e **não** aborta o relato).

### 6. Stack Tecnológico Sustentando as Features

[fala] *Cada peça da stack existe para sustentar uma feature concreta:*

| Camada | Tecnologia | Feature que sustenta |
|---|---|---|
| **Persistência (DB)** | SQLite + SQLAlchemy (ORM síncrono) | Relatos, encaminhamentos, votos, comentários, filtros salvos, usuários. **SQL é a fonte da verdade dos filtros**; FK enforcement via PRAGMA. |
| **Busca vetorial (Chroma)** | ChromaDB + sentence-transformers (`intfloat/multilingual-e5-small`) | Busca semântica, similares, e o **ranqueamento** do `POST /reports/query`. Padrão-chave: **ChromaDB só ranqueia; o SQL filtra** (`rank(query, ids) → scores`). Duas coleções: relatos e self-docs (helper). |
| **Clusterização léxica** | scikit-learn (TF-IDF + K-means) | Palavras-chave do subconjunto filtrado (`/reports/keywords`) — sem modelo de embedding, barato. |
| **LLM** | Ollama (local, `qwen3:8b`, padrão) **ou** Anthropic (configurável por env var) | Chat RAG sobre relatos, NL→filtro, helper da plataforma. **Privacidade:** com Ollama, o texto dos relatos **fica local**; só com `provider=anthropic` trechos vão para a API. |
| **Auth** | JWT Bearer (PyJWT, HS256, 24h) | Papéis citizen/agent/admin; acesso por recurso (BOLA-safe: recurso de terceiro retorna 404). |
| **Frontend** | React 18 + Vite + TS + Tailwind + react-leaflet (Zustand + react-query) | Workspace em grid, mapa, visões intercambiáveis; buildado para `static/` e servido pelo próprio FastAPI. |
| **Degradação graciosa** | — | Sem Ollama/Chroma configurados, os endpoints de IA retornam **503** e o resto do sistema segue de pé. |
| **Deploy** | Dockerfile multi-stage (node build → python:3.13-slim), Railway, `/health` | Tudo configurável por env var; `/data` é volume persistente. |
| **Testes** | pytest (backend) + vitest (frontend) | — |

[fala — fecho] *A escolha de stack reflete a tese do projeto: IA local e barata (Ollama, e5-small, TF-IDF) como **assistente auditável** — cada resposta cita sua fonte, nada é auto-aplicado, e a arquitetura limpa mantém a IA atrás de portas plugáveis. O humano permanece no comando da curadoria.*

---

## Recomendações

1. **(Medium) Use o arco em 6 slides** problema → casos de uso → jornadas → features → arquitetura → stack, espelhando exatamente o pedido. É a estrutura acima.
2. **(Medium) Seja explícito sobre o escopo entregue vs. idealizado** na seção de features (e/ou num slide "trabalho futuro"): IA de categorização + evento de curadoria + few-shot **não** foram implementados. Para uma banca de IA Systems Design, honestidade sobre o que ficou como hipótese de design é mérito, não demérito — e evita a armadilha já apontada no research-000185.
3. **(Low) Destaque os 2 princípios de arquitetura** (IA atrás de portas em `infrastructure/`; auth centralizada com author_id do token) como as decisões que tornam o sistema testável e seguro — bom material para perguntas da banca.
4. **(Low) Enfatize o padrão "SQL filtra, Chroma ranqueia"** e a privacidade do LLM local (Ollama) — são os pontos tecnicamente mais interessantes da stack de IA.
5. **(Opcional) Material pronto reaproveitável:** `_output/communication/2026-06-21/communication-000128-academics.{md,html}` e `communication-000184-academics` já têm conteúdo acadêmico; este discurso pode virar um `/communicate` para a audiência ACD (academics) se quiser slides/HTML gerados.

## Q&A log

**Q1 (inicial):** eu quero comunicar para os professores o que foi implementado no fala-gavea — discurso problema → casos de uso → jornadas → features → arquitetura → stack (db, chroma, llm).

**A1:** Montei o roteiro completo acima, em 6 seções alinhadas ao pedido. **Problema:** laço quebrado nas duas pontas — cidadão sem canal/transparência (R-PS-001) e agente sem visão geoespacial/semântica para agrupar demandas similares (R-PS-002). **Casos de uso:** US-001 (registrar relato georreferenciado), US-002 (encaminhar agregando N relatos a 1 órgão), US-003 (explorar por busca semântica + chat que cita fontes). **Jornadas:** JM-TB-001/002/003, todas implementadas ponta a ponta, com o workspace em grid de visões intercambiáveis e defaults por papel. **Features:** registro (com anônimo), mapa público + transparência sem login, votos/comentários, encaminhamento como agregação com ciclo de status, e a camada de IA-assistente (busca semântica, similares, NL→filtro que nunca auto-aplica, chat RAG com citações, palavras-chave TF-IDF, helper da plataforma, AiBadge). **Crucial:** sinalizei o que NÃO foi entregue (sugestão de categoria por IA, evento de curadoria, few-shot loop — hipótese de design, conforme research-000185). **Arquitetura:** clean architecture em 4 camadas com IA sempre atrás de portas em `infrastructure/` e auth centralizada. **Stack:** SQLite/SQLAlchemy (fonte da verdade dos filtros), ChromaDB+e5-small (só ranqueia), TF-IDF/K-means, LLM Ollama-local-ou-Anthropic (RAG com citações), JWT, React SPA servida pelo FastAPI, com degradação graciosa (503) e deploy Docker/Railway.

## Recommendations summary

- **Medium** — Apresentar no arco de 6 seções problema → casos de uso → jornadas → features → arquitetura → stack (roteiro pronto acima).
- **Medium** — Marcar explicitamente o escopo entregue vs. idealizado (sem IA-categorização / evento de curadoria / few-shot) para honestidade perante a banca.
- **Low** — Destacar os 2 princípios de arquitetura (IA atrás de portas; auth centralizada com author_id do token).
- **Low** — Enfatizar "SQL filtra, Chroma ranqueia" e a privacidade do LLM local.
- **Opcional** — Reaproveitar communication-000128/000184 (academics) ou rodar `/communicate` ACD para gerar slides/HTML.
