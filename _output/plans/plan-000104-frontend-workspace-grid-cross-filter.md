# Plan 000104 | fala-gavea/workspace-grid | 2026-06-19 21:31 UTC | Frontend iteration 1: workspace grid + cross-filter + IA widgets | Review: standard
plan_format_version: 1
source: research-000092

## User Brief

the 1st frontend iteration — grid/workspace shell + Zustand filter/selection store + lift filter out of
MapPage + Mapa/Tabela with cross-filter + wire Tópicos (GET /reports/topics), similares, and RAG chat
(POST /chat) to the done backends. Pass source: research-000092

## Agent Interpretation

**Problem**: O SPA é *map-centric* — a rota `/` é o `MapPage` em tela cheia, o filtro vive em `useState`
local (`MapPage.tsx:31`), e as features de IA (busca semântica, chat) são placeholders desabilitados.
A jornada JM-TB-003 (formalizada em product-design-as-intended.md §15) pede um **workspace**: filtro
lateral compartilhado alimentando **visões intercambiáveis** sobre o mesmo conjunto de relatos, com os
backends de IA (Wave 1/2) — já prontos — ligados como widgets de primeira classe.

**Approach** (research-000092 R1–R3, R5–R6): introduzir um **store Zustand** como fonte única de verdade
do filtro/seleção/visões; react-query continua dono do cache de servidor. A rota `/` passa a renderizar
um `WorkspacePage` (FilterPanel à esquerda + barra de toggles + grade de visões ativas). O `MapPage` é
refatorado: seu conteúdo de mapa vira o widget `MapView`; `SelectionBar` + `CreateForwardingDialog` sobem
para o workspace e ficam acessíveis do Mapa **e** da Tabela. Visões de IA (Tópicos, Similares, Chat RAG)
são novos widgets que consomem `GET /reports/topics`, `GET /reports/{id}/similar` e `POST /nl/chat`.
Visibilidade inicial das visões definida pelo papel (R3).

**Escopo desta iteração** (fiel ao brief): Mapa, Tabela, Tópicos, Similares, Chat RAG + filtro de texto
semântico no painel. **Fora de escopo**: widget de Gráficos agregados/Recharts (research-000092 R4 — fica
para a iteração 2), layouts salvos/drag-resize, colapso mobile completo (R7 — placeholder mínimo aqui; a
perspectiva de responsividade fica explicitamente adiada, não é descuido).

**Linha de corte** (sequenciamento, ver Steps 5/12): **Fase A+B (Steps 1–7) é a fatia entregável (MVP
Mapa+Tabela com cross-filter)**; **Fase C (Steps 8–10) é deferível por-visão** se um provedor de IA estiver
indisponível no dev. A remoção do `MapPage` (Step 12) depende só dos Steps 4–7.

**Alternatives rejected**:
- *Context API em vez de Zustand*: re-renderiza todos os widgets a cada tecla de filtro (research-000092 R1).
- *Manter filtro server-side por interação*: round-trip por clique de cross-filter trava a 10k relatos;
  usamos cross-filter em memória sobre o conjunto buscado (R5), com commit server-side só nos filtros
  estruturados/`bbox`/texto-semântico.

## Dependencies

- Backends prontos (verificados): `GET /reports/geojson` (filtros estruturados + bbox), `GET /reports/search?q=`
  (busca semântica → `list[ReportSearchResult]`, pública), `GET /reports/{id}/similar?n=` (similares,
  precisa de `search_port`), `GET /reports/topics` (**requer autenticação** + `min_docs`, retorna
  `{topics:[{topic_id,terms[],count}], total_reports}`), `POST /nl/chat` (**agent/admin**, body
  `{message, session_id?}` → `{response, cited_report_ids}`).
- Nota: o chat está montado em **`/nl/chat`** (prefixo `/nl` em `main.py:38`), não `/chat`.
- Tópicos/Similares/Chat retornam **503** quando o provedor semântico/LLM não está configurado — os
  widgets tratam 503 com mensagem "indisponível", sem quebrar o workspace.

## Files

### New
- `frontend/src/store/workspaceStore.ts` — store Zustand (filtros, seleção, visões ativas, seed de similares)
- `frontend/src/features/workspace/WorkspacePage.tsx` — shell: FilterPanel + ViewToggleBar + grade de visões
- `frontend/src/features/workspace/FilterPanel.tsx` — filtro lateral (move FiltersSidebar + texto semântico + contagem viva `aria-live`)
- `frontend/src/features/workspace/ViewToggleBar.tsx` — liga/desliga visões; auto-explicação por visão
- `frontend/src/features/workspace/views/MapView.tsx` — mapa como widget (clustered + desenho de bbox → store)
- `frontend/src/features/workspace/views/TableView.tsx` — lista/tabela dos relatos filtrados, linhas selecionáveis
- `frontend/src/features/workspace/views/TopicsView.tsx` — `GET /reports/topics` (agente/admin)
- `frontend/src/features/workspace/views/SimilarsView.tsx` — `GET /reports/{id}/similar` (fora do filtro)
- `frontend/src/features/workspace/views/ChatView.tsx` — `POST /nl/chat` (agente/admin), cita `cited_report_ids`
- `frontend/src/hooks/useFilteredReports.ts` — fonte única: geojson + interseção com busca semântica
- `frontend/src/hooks/useTopics.ts`, `frontend/src/hooks/useSimilarReports.ts`, `frontend/src/hooks/useSemanticSearch.ts`, `frontend/src/hooks/useChat.ts`
- `frontend/src/store/workspaceStore.test.ts`, `frontend/src/features/workspace/FilterPanel.test.tsx`, `frontend/src/features/workspace/views/TableView.test.tsx`

### Modified
- `frontend/src/lib/types.ts` — `TopicItem`, `TopicListResponse`, `ReportSearchResult`, `ChatRequest`, `ChatResponse`, `WorkspaceFilters`
- `frontend/src/lib/api.ts` — `getTopics`, `getSimilarReports`, `searchReports`, `chat`
- `frontend/src/App.tsx` — rota `/` → `WorkspacePage` (lazy) no lugar de `MapPage`
- `frontend/src/features/map/SelectionBar.tsx` / `CreateForwardingDialog.tsx` — consumir store (seleção do Mapa e da Tabela)
- `frontend/src/features/map/ReportMarkers.tsx` — clustering de marcadores
- `frontend/package.json` — `zustand`, `react-leaflet-cluster` (+ `@types`)

### Removed / retired
- `frontend/src/features/map/MapPage.tsx` e `FiltersSidebar.tsx` — conteúdo migrado para `MapView`/`FilterPanel`; remover após migração (atualizar/remover `FiltersSidebar.test.tsx`)

## Best Practices

- Store Zustand com **selectors** por fatia (`useWorkspaceStore(s => s.filters)`) para isolar re-render por widget.
- react-query continua **único** dono de dados de servidor; o store guarda só estado de UI (filtro/seleção/visões).
- `Set<string>` para `selectedIds` — converter para array só na borda (CreateForwardingDialog/API).
- Cross-filter **em memória**: `useFilteredReports` busca o geojson por filtros estruturados (commit server-side)
  e, quando há texto semântico, busca `/reports/search` e devolve a **interseção** ordenada por score.
- a11y (research-000092 R6): toda mudança de filtro emite resumo em `aria-live="polite"`; desenho de bbox
  tem caminho alternativo por botão (limpar/aplicar) com alvos ≥44px; urgência usa forma+texto além de cor.
- Widgets de IA degradam com graça em 503 (mensagem "indisponível", não erro fatal).
- TypeScript estrito (sem `any`); manter padrão shadcn-style dos componentes `ui/`.

## Design Decisions

**User-visible impact**: A rota `/` vira um workspace. À esquerda, o usuário filtra (tipo, urgência, status,
data, **texto semântico**) e vê a contagem viva. Ao centro, liga/desliga visões: Mapa (desenha área = filtro
`bbox`), Tabela (lê o texto dos relatos, seleciona para encaminhar), Tópicos (temas do subconjunto), Similares
(relatos parecidos a um relato-semente, **ignorando o filtro**) e Chat RAG (pergunta em NL, recebe resposta
com relatos citados). Cidadão/anônimo vê Mapa+Tabela; agente/admin vê as cinco visões.

**Trade-offs accepted**:
- **Texto semântico × filtros estruturados**: interseção client-side ordenada por score semântico. Simples e
  testável; pode não escalar a corpora enormes, mas serve ao PoC (research-000092, questão em aberto resolvida assim).
- **Clustering de marcadores**: adiciona `react-leaflet-cluster` (necessário a ~10k seeds; R5). Se a integração
  com react-leaflet v4 atritar, o passo 6 pode cair para render simples sem cluster sem bloquear o resto.
- **Tópicos exige login**: a visão Tópicos fica oculta para anônimo (backend pede `current_user`); coerente
  com a visibilidade por papel.

**Metacommunication impact**: Eu te dou um workspace onde *você* decide como ler os relatos — o filtro é seu e
único, e cada visão (mapa, lista, temas, similares, chat) olha o mesmo conjunto de ângulos diferentes. A IA
aparece como mais uma lente de exploração, sempre citando de onde tirou as respostas — assistência, não decisão.

## Steps

### Fase A — Fundação (store + contratos + shell)

**Step 1 — Dependências e tipos**
- `package.json`: adicionar `zustand`, `react-leaflet-cluster` (e tipos se necessário). `npm install`.
- `types.ts`: adicionar `TopicItem {topic_id:number; terms:string[]; count:number}`, `TopicListResponse
  {topics:TopicItem[]; total_reports:number}`, `ReportSearchResult` (= `ReportDetail` + `score:number`),
  `ChatRequest {message:string; session_id?:string}`, `ChatResponse {response:string; cited_report_ids:string[]}`,
  `WorkspaceFilters` (= `ReportFilters` + `semanticQuery?:string`).
- Docs: N/A

**Step 2 — Camada de API**
- `api.ts`: `getTopics(filters, min_docs=3)` → `GET /reports/topics{query}` (envia token);
  `getSimilarReports(id, n=5)` → `GET /reports/{id}/similar?n=`; `searchReports(q, n=50)` → `GET /reports/search?q=&n=`
  (**`n=50`** = teto do backend; evita truncar silenciosamente o conjunto cross-filtrado — ver Step 5/11);
  `chat(body: ChatRequest)` → `POST /nl/chat`. Reusar `buildQuery`/`request` existentes.
- `getTopics` e `chat` **não** capturam 401 localmente: token expirado/insuficiente cai no handler global
  `auth:unauthorized` de `request()` (`api.ts:60`). Só **503** é tratado inline pelos widgets.
- Docs: N/A

**Step 3 — Store Zustand**
- `workspaceStore.ts`: estado `{ filters: WorkspaceFilters; selectedIds: Set<string>; activeViews: ViewId[];
  similarSeedId: string | null }` + ações `setFilter(patch)`, `clearFilters()`, `setBbox(bbox|undefined)`,
  `setSemanticQuery(q)`, `toggleSelect(id)`, `clearSelection()`, `toggleView(id)`, `setSimilarSeed(id)`.
  `ViewId = 'map'|'table'|'topics'|'similars'|'chat'`. Helper `defaultViewsForRole(role)`.
- Expor um selector `structuredFilters` que devolve **só** `{type_id, urgency, status, since, until, bbox}`
  (exclui `semanticQuery`), para os hooks de cache de servidor chavearem apenas pelos filtros estruturados —
  uma tecla no campo semântico nunca refaz o fetch do geojson.
- Tests: `workspaceStore.test.ts` (toggleSelect idempotente, clearFilters preserva seleção?/decisão, setBbox).
- Docs: N/A

**Step 4 — Shell do workspace + roteamento**
- `WorkspacePage.tsx`: layout flex — `FilterPanel` (rail esquerdo) + área central com `ViewToggleBar` + grade das visões em `activeViews`.
  Inicializa `activeViews` por papel (via `useAuth`) na montagem.
- `ViewToggleBar.tsx`: chips/botões liga-desliga por visão, cada um com rótulo + 1 linha de auto-explicação;
  esconder Tópicos/Chat para quem não é agente/admin. **a11y:** cada toggle expõe `aria-pressed` refletindo
  on/off, nome acessível = rótulo + auto-explicação, e **gerencia foco** ao desligar uma visão (foco volta
  para a barra de toggles, não se perde para `<body>`).
- `App.tsx`: trocar import lazy de `MapPage` por `WorkspacePage` na rota `/`.
- Docs: drr (nova jornada/UX pattern já em design intent; registrar em as-coded via post-skill)

### Fase B — Visões base (Mapa + Tabela) com cross-filter

**Step 5 — Fonte única filtrada**
- `useFilteredReports.ts`: passa **só** o selector `structuredFilters` para `useReports` (geojson); roteia
  `semanticQuery` exclusivamente para `useSemanticSearch`. Se `semanticQuery`, devolve **interseção** (features
  cujo `id` está nos resultados de busca), ordenada por score. Expõe
  `{ features, count, isLoading, semanticActive, semanticTruncated }`.
- **Contrato de loading/ordenação:** `isLoading` é true enquanto a query do geojson **ou** (quando
  `semanticActive`) a de busca estiver pendente; reter o resultado anterior via react-query
  `placeholderData: keepPreviousData` para não piscar vazio ao trocar filtro.
- **Truncamento:** quando `semanticActive` e o conjunto de busca está no teto (50), setar `semanticTruncated: true`
  para o FilterPanel anunciar (Step 11).
- Tests (**obrigatório**): teste do helper de interseção (match por id + ordenação por score + flag de truncamento).
- Docs: N/A

**Step 6 — MapView (mapa como widget) + clustering + bbox**
- `MapView.tsx`: migrar `MapContainer`/`TileLayer`/`ReportMarkers` do `MapPage`. Marcadores via
  `react-leaflet-cluster`. Adicionar controle de **desenhar área** → `setBbox` (com botão "Aplicar/Limpar área"
  acessível por teclado, alvos ≥44px — caminho alternativo ao arraste). Lê features de `useFilteredReports`.
- `ReportMarkers.tsx`: envolver em cluster; seleção continua via store.
- **a11y:** a `TableView` é o equivalente acessível por teclado do mapa; o caminho alternativo de bbox por
  teclado (botões Aplicar/Limpar ≥44px) é obrigatório, mas operabilidade total dos marcadores por teclado não
  é (os mesmos relatos são alcançáveis pela Tabela). Se `react-leaflet-cluster` atritar com react-leaflet v4,
  cair para render sem cluster sem bloquear o resto.
- Docs: N/A

**Step 7 — TableView + seleção compartilhada + SelectionBar/Dialog**
- `TableView.tsx`: tabela (`components/ui/table`) com texto, tipo, urgência (forma+cor+texto), status, data;
  linhas selecionáveis (checkbox) escrevendo `toggleSelect` no store; lê de `useFilteredReports`.
- `SelectionBar.tsx`: passa a ler `count`/`onClear`/`onCreateForwarding` a partir do store (seleção do Mapa
  **e** da Tabela). `CreateForwardingDialog` **permanece prop-driven** — recebe `Array.from(selectedIds)` na
  borda (já aceita `selectedIds: string[]`); não acoplar o Dialog ao store.
- Renderizar `SelectionBar` + `CreateForwardingDialog` no `WorkspacePage` **apenas quando `isAgent`**
  (preserva o gate atual de `MapPage.tsx:101,121`).
- Tests: `TableView.test.tsx` (render + toggle de seleção).
- Docs: N/A

### Fase C — Visões de IA (ligadas aos backends prontos)

**Step 8 — TopicsView**
- `useTopics.ts` + `TopicsView.tsx`: `GET /reports/topics` com os mesmos filtros estruturados/bbox; mostra
  cada tópico (top termos + contagem) e `total_reports`. Estados (todos em `role="status"`/`aria-live="polite"`):
  loading; lista vazia (corpus < min_docs) → mensagem amigável; 503 → "Análise de tópicos indisponível".
  401 não é tratado aqui (handler global). Visível só para agente/admin (gate de UI; backend exige auth).
- Docs: N/A

**Step 9 — SimilarsView (fora do filtro)**
- `useSimilarReports.ts` + `SimilarsView.tsx`: a partir de `similarSeedId` (definido ao clicar "ver similares"
  num popup do mapa / linha da tabela), `GET /reports/{id}/similar`. **Caption persistente** (não só placeholder):
  "Similares em toda a base, fora do filtro" — previne a ruptura de modelo mental "filtrado × similar"
  (JM-TB-003 passo 6). Estados loading/vazio/sem-seed anunciados via `role="status"`.
- Docs: N/A

**Step 10 — ChatView (RAG)**
- `useChat.ts` (mutation) + `ChatView.tsx`: `POST /nl/chat` com `{message}`. Resposta do assistente e a
  mensagem 503 "Assistente indisponível" dentro de uma região `aria-live="polite"` (leitor de tela ouve a
  resposta). `cited_report_ids` como **`<button>` reais** (focáveis por teclado), clicar → foca/destaca relato
  no Mapa/Tabela (opcional nesta iteração: destacar/scrollar). Só agente/admin; 401 cai no handler global.
- Substituir o placeholder de chat antigo (removido junto com `MapPage`).
- Docs: contextual-help (opcional) — auto-explicação de cada visão

### Fase D — a11y, limpeza e testes

**Step 11 — a11y do cross-filter + contagem viva**
- `FilterPanel.tsx`: região `aria-live="polite"` anunciando "N relatos" e a mudança de filtro aplicada
  (ex: "Filtro: urgência alta — 142 relatos"). Quando `semanticTruncated` (Step 5), anunciar o teto:
  "Filtro: urgência alta — mostrando os 50 relatos mais relevantes para 'poste apagado'". Campo de texto
  semântico habilitado (remove placeholder "em breve"). Urgência/legendas com forma+texto além de cor.
- Docs: N/A

**Step 12 — Limpeza e testes**
- Remover `MapPage.tsx` e `FiltersSidebar.tsx` — **contingente apenas aos Steps 4–7 verdes** (fatia MVP
  Mapa+Tabela), **não** à Fase C. Os Steps 8–10 (Tópicos/Similares/Chat) são **deferíveis por-visão** se o
  provedor semântico/LLM não estiver disponível no ambiente de dev; o workspace pode subir só com Mapa+Tabela.
- Atualizar/remover `FiltersSidebar.test.tsx`, `CreateForwardingDialog.test.tsx` conforme nova fonte de seleção (store).
- `FilterPanel.test.tsx` (aplica filtro → atualiza store + contagem). `npm run test`, `npm run lint`,
  `npm run build` verdes.
- Docs: N/A

## Test plan

1. `cd frontend && npm install` instala `zustand` e `react-leaflet-cluster` sem conflito de peer-deps.
2. `npm run build` e `npm run lint` passam (TS estrito, sem `any`).
3. `npm run test` — store, FilterPanel e TableView verdes.
4. Manual (com backend + Ollama + dados ingeridos): em `/`, anônimo vê Mapa+Tabela; aplicar filtro de tipo
   atualiza Mapa e Tabela e a contagem `aria-live`; desenhar área no mapa filtra por bbox; digitar texto
   semântico reordena/interseca o conjunto.
5. Manual como **agente**: visões Tópicos, Similares e Chat aparecem; Tópicos lista temas do subconjunto
   filtrado; clicar "similares" de um relato mostra similares fora do filtro; Chat responde e cita relatos;
   selecionar relatos na Tabela e no Mapa habilita "Criar encaminhamento".
6. Sem provedor semântico/LLM: Tópicos/Similares/Chat mostram "indisponível" (503) sem quebrar o workspace.

## Docs

- DRR / as-coded: registrar a implementação de JM-TB-003 e do padrão §8 "Workspace em grid" em
  `product-design-as-coded.md` (post-skill) e propor flip de `STATUS: implemented` quando verificado.
  Reconciliar `POST /chat` → `POST /nl/chat` no registro as-intended/as-coded (§15 ainda cita `/chat`).
- Contextual-help (opcional): microcopy de auto-explicação por visão.

## Review Log

Plan-reviewer, **standard** depth (4/6 deep-dives, 1 iteração, convergido). Shortlist: API, ARCH, A11Y,
SEC, UX, TEST, PERF (DB/I18N N/A). **Adopted:** SEC (sem nova superfície; auth servidor + gate de UI são
complementares; C1 local-only e S3 LLM read-only não violados — todas as chamadas de IA vão a endpoints
locais), TEST (testes de store/FilterPanel/TableView; gap do helper de interseção dobrado no Step 5).
**Deferred → resolvido em emendas:**
- **API:** rotas confirmadas; `/topics` e `/nl/chat` retornam 401 antes do 503 (delegado ao handler global);
  `searchReports` `n=20` truncava o conjunto cross-filtrado → `n=50` + anúncio de truncamento (Steps 2, 5, 11).
- **ARCH:** separação react-query/Zustand sólida; fatiar `structuredFilters` para não refazer fetch do geojson
  a cada tecla semântica; contrato de loading com `keepPreviousData` (Steps 3, 5).
- **A11Y:** `aria-pressed` + gestão de foco nos toggles; `role="status"`/`aria-live` em Tópicos/Similares/Chat;
  chips de citação como `<button>`; TableView como equivalente acessível do mapa (Steps 4, 6, 8, 9, 10).
- **UX/escopo:** linha de corte explícita (A+B = MVP; C deferível por-visão); preservar gate `isAgent` e manter
  Dialog prop-driven (Steps 7, 12, Escopo).
Sem conflitos inter-perspectiva. Nenhum achado exigiu re-plano estrutural.
