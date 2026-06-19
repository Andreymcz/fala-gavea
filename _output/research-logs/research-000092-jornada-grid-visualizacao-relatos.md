# Research 000092 | FEAT -O | 2026-06-19 13:27 UTC | Jornada de grid para visualização, busca e análise dos relatos

tags: ux, frontend-architecture, dashboard, semantic, accessibility

**User brief:** criar jornada de visualização, busca e análise dos relatos. ao invés do mapa ser o centro da visualização, ele é apenas mais uma forma. o painel central da aplicação é um grid, que pode conter diversas ferramentas para visualizar os relatos filtrados. pensar educacionalmente nos dois projetos: (1) Canal Digital Comunitário para Segurança Urbana (Waze comunitário); (2) Mapa Colaborativo de Dados para Segurança e Planejamento do Bairro.

**Agent interpretation:** Inverter o modelo atual *map-centric* do SPA (rota `/` = `MapPage` em tela cheia) para um modelo *workspace/dashboard*: o painel central vira um **grid de ferramentas** onde o mapa é apenas um widget. O mesmo conjunto de *relatos filtrados* alimenta todos os widgets, ligados por cross-filtering. Definir a jornada de exploração/análise (JM-TB-003), o conjunto de widgets da primeira iteração, e a arquitetura de frontend (estado compartilhado, charting, sequenciamento) que suporta os dois projetos educacionais.

**Files reviewed:** `frontend/src/features/map/MapPage.tsx`, `frontend/src/hooks/useReports.ts`, `frontend/src/features/map/ReportMarkers.tsx`, `frontend/src/features/map/SelectionBar.tsx`, `product-design/project/product-design-as-coded.md`, `product-design/project/product-design-as-intended.md` (§14-§16), `_output/roadmaps/roadmap-00002-wave2-espacos-semanticos-ia.md`

**Decisions já tomadas pelo time (entradas, não em discussão):**
1. **Audiência:** um único grid público servindo TANTO o cidadão (transparência cívica — projeto 1) QUANTO o agente (análise territorial — projeto 2).
2. **Widgets da iteração 1 (4):** Mapa (Leaflet, existente), Tabela/lista, Gráficos agregados (contagens por tipo/urgência/status + série temporal), Tópicos/clusters semânticos (BERTopic) + similares.
3. **Layout:** base fixo com **toggle** de quais widgets aparecem (sem drag/resize/layouts salvos).
4. **Interação:** **linked views** / cross-filtering — todos os widgets compartilham um filtro central; interagir com um refiltra os demais.

---

## Q&A Log

### Q1

**User:** Criar jornada de visualização, busca e análise dos relatos. Ao invés do mapa ser o centro da visualização, ele é apenas mais uma forma — o painel central da aplicação é um grid que pode conter diversas ferramentas para visualizar os relatos filtrados. Pensar educacionalmente nos projetos "Canal Digital Comunitário" (Waze comunitário) e "Mapa Colaborativo de Dados".

**Answer:**

#### Estado atual vs. visão

| Dimensão | Hoje (map-centric) | Visão (workspace/grid) |
|---|---|---|
| Rota `/` | `MapPage` em tela cheia | Workspace com grid de widgets |
| Visualização | O mapa **é** a visualização | O mapa é **um** widget entre vários |
| IA semântica | Placeholders desabilitados sobre o mapa | Widget de tópicos/similares de 1ª classe |
| Filtro | `useState` local no `MapPage` | Store de filtro **compartilhado** entre widgets |
| Análise | Inexistente (só ver marcadores) | Gráficos + tabela + clusters cruzados |

O modelo de grid serve os dois projetos porque **o substrato de dados é o mesmo** (os relatos filtrados); o que muda entre cidadão e agente é a *intenção*, não o *conteúdo*. O cidadão usa o painel para **acompanhar** (Waze comunitário: ver problemas, ver melhorias); o agente usa para **ler padrões e priorizar** (Mapa Colaborativo: identificar prioridades, visualizar padrões, pactuar soluções). Isso valida a decisão de painel único — desde que a *visibilidade inicial* dos widgets seja sensível ao papel.

#### Mapeamento aos dois projetos educacionais

- **Projeto 1 (Canal Digital / Waze comunitário):** transformar percepção individual em informação coletiva e acionável. No grid: o **Mapa** + **Tabela** dão a camada de transparência e acompanhamento; os **Gráficos** ("melhorias realizadas", status ao longo do tempo) divulgam o progresso e a corresponsabilidade.
- **Projeto 2 (Mapa Colaborativo de Dados):** transformar dados em ferramenta de leitura do território e planejamento. No grid: **Tópicos/clusters semânticos** + **Gráficos agregados** + **cross-filtering** são exatamente a leitura de padrões e priorização; a dimensão **educativa** (formar moradores/jovens a interpretar dados) se traduz em widgets que **se auto-explicam** — cada ferramenta diz o que é e como lê o território.

#### A jornada proposta (esboço de JM-TB-003)

> **JM-TB-003: Explorar, buscar e analisar relatos no workspace** — Persona: cidadão (R-P-001) e agente (R-P-002).

| # | Ação | Touchpoint | Emoção | Pain point | Oportunidade |
|---|------|-----------|--------|-----------|-------------|
| 1 | Acessa `/` e vê o workspace (grid) com filtro central | Grid | Orientado | "Não é pra mim" se parecer um dashboard de analista | **Defaults por papel**: cidadão vê Mapa+Tabela; agente vê os 4 widgets |
| 2 | Aplica filtros (tipo/urgência/status/data) na barra central | FilterBar compartilhada | Analítico | — | Contagem viva ("142 relatos") em `aria-live` |
| 3 | Liga/desliga widgets via toggle | Toggle de ferramentas | No controle | Não saber o que cada widget faz | Rótulo + 1 linha de auto-explicação por widget |
| 4 | Clica num tópico / pincela um período / seleciona área no mapa | Qualquer widget | Curioso | Refiltro silencioso confunde | Cross-filter **anunciado** ("Filtro: urgência alta") |
| 5 | Lê padrões nos gráficos e no clustering | Charts + Topics | Perspicaz | IA pode ser imprecisa | Deixar claro que IA é assistência, não verdade |
| 6 | (Agente) seleciona relatos no mapa **ou** na tabela | Map/Table → SelectionBar | Deliberativo | Seleção presa só ao mapa hoje | `selectedIds` no store compartilhado → SelectionBar única |
| 7 | (Agente) cria encaminhamento a partir da seleção | CreateForwardingDialog | Decisivo | — | Fluxo preservado, agora multi-widget |

Esta jornada deve ser formalizada em `product-design-as-intended.md §15` via `/design` (ver "Próximos passos").

---

## Avaliação por perspectiva

A avaliação multi-perspectiva (UX, arquitetura de frontend, performance, acessibilidade, manutenibilidade/DX, responsividade, comunicabilidade/semiótica) foi conduzida pelo `research-reviewer`. Síntese:

### UX & Comunicabilidade (semiótica)
Painel único para duas personas opostas (cidadão ocasional/mobile/novato × agente diário/desktop/intermediário) é **defensável** porque os dados são os mesmos, mas gera risco semiótico de rupturas "Onde estou? / Isto não é pra mim" (IIb1) e "O que é isto?" (IIc1) — o cidadão pode cair num "dashboard de analista". **Mitigação:** mesma estrutura de painel, **visibilidade inicial dos widgets por papel**, e cada widget **auto-explicativo** (rótulo + microcopy). Como o curso é de design HCI, a comunicabilidade é critério de primeira classe.

### Arquitetura de frontend & estado
A decisão *load-bearing* é o **contrato de filtro compartilhado**. Hoje `MapPage` mantém `mapFilters` em `useState` local e alimenta `useReports(apiFilters)`. Para linked views, esse estado **sobe** para um store compartilhado: uma fonte única de verdade do filtro, N widgets consumidores que *leem* o filtro e *propõem* deltas (clique em tópico → filtro de tópico; brush de tempo → `since/until`; bbox do mapa → `bbox`). Mantém-se a arquitetura limpa: react-query continua dono do cache de servidor; o store de UI é separado.

### Performance (≈10k relatos)
`ReportMarkers` renderiza 1 marcador por feature **sem clustering** — 10k marcadores travam no mobile do cidadão (bug latente, independente do redesign). Decisões acopladas: (a) **clustering** de marcadores (Leaflet.markercluster / supercluster); (b) **filtrar em memória** o conjunto já buscado para interações rápidas, reservando round-trip ao `GET /reports/geojson` para a carga inicial grosseira e *commits* explícitos de filtro. GeoJSON de 10k ≈ 1–3 MB: busca uma vez por filtro grosseiro, cross-filtra em memória → updates sub-frame sem latência de rede por interação.

### Acessibilidade
Linked views é o padrão **mais hostil a a11y** da proposta, e o framework trata a11y como não-negociável. Brush e bbox-select são gestos de arraste (precisam de caminho alternativo via botão/teclado, alvos ≥44px); segmentos de gráfico que filtram precisam de foco de teclado e equivalente textual/tabela; urgência hoje é **só cor** (precisa de forma/texto adicional). Cada cross-filter deve emitir um resumo `aria-live` ("Filtro aplicado: urgência alta, 142 relatos") — refiltro silencioso de 4 widgets é a ruptura "O que aconteceu?".

### Manutenibilidade / DX (time de 5)
Tooling deve tender ao **mínimo que funciona**. Faltam lib de estado e lib de charting — preencher minimamente. Redux Toolkit / framework de dashboard pesado é o risco de DX ("Obrigado, mas não" — o time contorna a ferramenta cara).

### Responsividade
Grid de 4 painéis é nativo de desktop; o cidadão é mobile-first. Definir **colapso mobile explícito**: em telas estreitas, **um widget ativo** com troca por abas (Mapa | Lista | Gráficos | Tópicos) compartilhando o filtro — não reflow de 4 painéis em scroll longo.

### Sequenciamento / risco de dependência
O widget de **Tópicos/clusters** depende de backend **não construído** (Wave 1 busca, Wave 2 `GET /reports/topics` + RAG). Não pode bloquear os outros três. Mapa e Tabela rodam 100% no `GET /reports/geojson` existente; Gráficos são agregação client-side pura. Topics entra por último, atrás de um placeholder digno.

---

## Recomendações (resumo acionável)

| # | Prioridade | Recomendação |
|---|-----------|--------------|
| R1 | **HIGH** | **Zustand** para o store de filtro/seleção compartilhado; **react-query** continua só com dados de servidor. Selectors do Zustand isolam re-render por widget (~1KB, pouco boilerplate) — Context re-renderiza tudo a cada tecla de filtro. |
| R2 | **HIGH** | **Sequenciar Mapa → Tabela → Gráficos → Tópicos.** Mapa+Tabela rodam no `GET /reports/geojson` atual (zero backend novo); Gráficos = agregação client-side; Tópicos por último, atrás de placeholder digno ("Análise semântica de tópicos — em breve") até Wave 1/2. |
| R3 | **HIGH** | **Papel define a visibilidade inicial dos widgets, não a estrutura do painel.** Cidadão/anônimo: Mapa+Tabela visíveis, Gráficos+Tópicos recolhidos. Agente/admin: os 4 + SelectionBar→CreateForwardingDialog acessível do Mapa **e** da Tabela (`selectedIds` no store compartilhado). |
| R4 | **MEDIUM** | **Recharts** como lib de charting — declarativo, SVG (tematizável com Tailwind), é a lib que o componente `Chart` do shadcn embrulha. Cobre contagens-por-categoria e série temporal out-of-the-box. (Visx: curva íngreme; Chart.js: canvas, a11y mais fraca.) |
| R5 | **MEDIUM** | **Cross-filter em memória**; round-trip ao servidor só em commits de filtro grosseiro. Adicionar **clustering de marcadores** ao widget de Mapa independentemente do redesign (10k marcadores sem cluster já é bug latente). |
| R6 | **MEDIUM** | **A11y em todo cross-filter:** brush/bbox com botão+teclado equivalente (alvos ≥44px); segmentos de gráfico com `role="button"` + foco; forma/texto além da cor na urgência; um `aria-live="polite"` por mudança de filtro. Orçar por widget, não como passada de limpeza. |
| R7 | **LOW** | **Definir o colapso mobile antes de construir o grid:** em viewport estreito, um widget ativo com switcher por abas (Mapa \| Lista \| Gráficos \| Tópicos) compartilhando o filtro — não reflow em scroll. |
| R8 | **LOW** | Substituir o placeholder de chat atual (`MapPage.tsx:109-117`, `opacity-50 cursor-not-allowed` + emoji cru) por um placeholder que **declara o que vem e por quê** — controle desabilitado sem explicação é ruptura "Desisto". |

### Próximos passos sugeridos
1. **`/design`** para formalizar **JM-TB-003** (jornada de exploração/análise) em `§15` e atualizar §8 (UX Patterns) com o modelo de workspace/grid + a decisão de defaults por papel.
2. **`/plan`** para a 1ª iteração (R1–R3, R5 clustering): shell do grid + store Zustand + lift do filtro/seleção + widgets Mapa e Tabela com cross-filter + placeholder de Tópicos. Passar `source: research-000092`.
3. Alinhar o widget de Tópicos com o sequenciamento das Waves 1/2 do `roadmap-00002` (busca semântica + `GET /reports/topics`).

---

## Recommendations summary

- **R1 (HIGH):** Zustand para store de filtro/seleção compartilhado; react-query só para dados de servidor.
- **R2 (HIGH):** Sequenciar Mapa → Tabela → Gráficos → Tópicos; Tópicos atrás de placeholder até Wave 1/2.
- **R3 (HIGH):** Papel define visibilidade inicial dos widgets (painel único preservado); SelectionBar→Forwarding do Mapa e da Tabela.
- **R4 (MEDIUM):** Recharts como lib de charting.
- **R5 (MEDIUM):** Cross-filter em memória + clustering de marcadores no widget de Mapa.
- **R6 (MEDIUM):** A11y em todo cross-filter (teclado, alvos ≥44px, não-só-cor, `aria-live`).
- **R7 (LOW):** Colapso mobile explícito (widget único + abas).
- **R8 (LOW):** Substituir placeholder de chat desabilitado por placeholder explicativo.
