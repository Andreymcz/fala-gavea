# Research 000190 | fala-gavea | 2026-06-28 23:02 UTC | Linkar relato selecionado do mapa com a tabela
tags: frontend, workspace, map-table-sync, state-management, ux

## User brief

> tem como linkar o relato selecionado do mapa com a tabela ?

## Agent interpretation

O usuário (perfil agente/admin no workspace) quer vincular o relato selecionado no
mapa (`MapView`) com a tabela (`TableView`). Na pergunta de esclarecimento, escolheu
**sincronização bidirecional completa**: clicar na linha da tabela deve centralizar/abrir
o marcador no mapa, e clicar no marcador deve focar a linha — um destaque de "relato
ativo" único, separado do multi-select da cesta (`selectedIds`).

## Files

- `frontend/src/store/workspaceStore.ts` — estado Zustand compartilhado (`selectedIds`, `toggleSelect`, `similarSeedId`)
- `frontend/src/features/workspace/views/MapView.tsx` — mapa (react-leaflet + MarkerClusterGroup)
- `frontend/src/features/workspace/views/TableView.tsx` — tabela paginada (50/página, server-side)
- `frontend/src/features/map/ReportMarkers.tsx` — render dos marcadores
- `frontend/src/features/map/ReportPopup.tsx` — popup do marcador (checkbox "Selecionar para encaminhar", gated por `isAgent`)
- `frontend/src/hooks/useFilteredReports.ts` — fonte de dados (mapa: `/reports/geojson` todos os pontos; tabela: `/reports/query` paginado)

---

## Resposta

**Sim, dá — e metade do caminho já existe.** Mapa e tabela já compartilham um
conjunto de seleção via o `workspaceStore` (Zustand). Hoje:

- `MapView` → `ReportMarkers` → `ReportPopup` tem um checkbox ("Selecionar para
  encaminhar") que chama `toggleSelect(id)`.
- `TableView` lê o mesmo `selectedIds` e pinta a linha de azul (`bg-blue-50`) quando
  `selectedIds.has(p.id)`.

Ou seja, marcar um relato no popup do mapa **já** destaca a linha na tabela (e
vice-versa). O que falta para a **sincronização bidirecional completa** que você pediu
é um conceito separado de "relato ativo/focado" (clique = navegar/focar, não
selecionar para a cesta) e a reação visual em cada view.

### O que precisa ser construído

**1. Novo estado `activeReportId` no store (separado de `selectedIds`).**
Há um precedente direto: `similarSeedId` já é um ponteiro de id único usado para
comunicação entre views (tabela → SimilarsView). Replicar o padrão:

```ts
activeReportId: string | null
setActiveReport: (id: string | null) => void
```

Manter `selectedIds` (cesta/encaminhar, multi-select) intocado. Decidir a semântica do
clique na linha: hoje o `onClick` da `<TableRow>` chama `toggleSelect`. Sugestão: clique
na linha = `setActiveReport` (foco); checkbox = `toggleSelect` (cesta). Isso muda o
comportamento atual de clicar-na-linha-seleciona — vale confirmar com o time.

**2. Mapa → Tabela (clicar no marcador foca a linha).**
- `ReportMarkers`: adicionar `eventHandlers={{ click: () => onActivate(id) }}` no `<Marker>`.
- `TableView`: ao mudar `activeReportId`, dar `scrollIntoView()` na linha (guardar um
  `ref` por linha) e aplicar um destaque distinto do azul da seleção (ex.: `ring-2 ring-blue-500`).

**3. Tabela → Mapa (clicar na linha centraliza/abre o marcador).**
- `MapView`: ao mudar `activeReportId`, achar as coords pelo `features` e chamar
  `map.setView([lat, lon], zoom)`. Abrir o popup do marcador exige um passo extra por
  causa do clustering (ver complicações abaixo).

### Complicações reais (onde mora o trabalho)

- **Clustering quebra o "abrir popup" programático.** Com `MarkerClusterGroup`, o
  marcador-alvo pode estar dentro de um cluster e nem estar renderizado. Para abrir o
  popup é preciso `clusterGroup.zoomToShowLayer(marker, () => marker.openPopup())`, o
  que exige refs para os marcadores (um `Map<id, L.Marker>`) e para o grupo de cluster.
  MVP: só `map.setView` (pan/zoom) sem abrir popup, ou soltar um marcador-destaque temporário.

- **Paginação server-side trava o "rolar até a linha" entre páginas.** A tabela busca
  uma página por vez (`/reports/query`, 50/página, offset no servidor). Se o relato
  clicado no mapa não estiver na página atual, não há como rolar até ele sem saber seu
  índice global na ordenação. Opções:
  - *(a)* Pragmático/MVP: rolar+destacar só se estiver na página atual; caso contrário,
    abrir o `Dialog` de detalhe (que já existe) — mas hoje o `dialogFeature` é buscado em
    `sorted` (só a página atual), então precisaria de um fetch-by-id do relato.
  - *(b)* Completo: endpoint/parâmetro que retorne a posição do id na ordenação, para
    calcular a página e navegar.

- **Mapa e tabela são queries diferentes.** Mapa usa `/reports/geojson` (todos os
  pontos), tabela usa `/reports/query` (paginado, e *ranqueado* quando há busca
  semântica). O id ativo pode existir num conjunto e não no outro (ex.: tabela em top-N
  semântico vs. mapa com todos os pontos). A reação precisa degradar com elegância
  quando o id não está presente na view.
  - Nota lateral: hoje `MapView` chama `useFilteredReports()` **sem** `allPoints: true`,
    então cai no `/reports/query` com `limit` default de 200 — não em `/reports/geojson`.
    Vale confirmar se o mapa deveria passar `allPoints: true`; isso afeta quais ids ele expõe.

### Escopo recomendado

- **MVP (alto valor, baixo risco):** `activeReportId` no store; Mapa→Tabela com
  scroll+highlight quando na página atual; Tabela→Mapa com `map.setView` (pan/zoom) +
  destaque visual. Adiar abertura de popup clusterizado e scroll cross-página.
- **Completo (fase 2):** fetch-by-id para abrir o Dialog em Mapa→Tabela cross-página;
  `zoomToShowLayer` para abrir o popup no mapa.

### Avaliação por perspectivas

- **Arquitetura:** reusar o padrão `similarSeedId` mantém consistência; estado único no
  store evita prop-drilling entre views lazy-loaded. Manter `activeReportId` ortogonal a
  `selectedIds` evita acoplar "foco" com "cesta".
- **UX:** clique na linha mudando de "selecionar" para "focar" é uma mudança de
  comportamento — precisa de decisão explícita do time para não confundir o agente.
  Destaque de foco deve ser visualmente distinto da seleção da cesta.
- **Performance:** `scrollIntoView` e `setView` são baratos; o risco é re-render em
  excesso — assinar `activeReportId` com seletor fino do Zustand.
- **Acessibilidade:** ao focar via mapa, mover foco de teclado para a linha
  (`aria-current`/`focus()`), não só scroll visual.

---

## Q&A log

**Q1 (2026-06-28):** tem como linkar o relato selecionado do mapa com a tabela ?

**A1:** Sim. Mapa e tabela já compartilham `selectedIds` no `workspaceStore` (marcar no
popup do mapa já pinta a linha na tabela). Para a **sincronização bidirecional completa**
escolhida, falta um estado de "relato ativo" (`activeReportId`, separado da cesta),
reações em cada view (scroll+highlight na tabela; `setView`+popup no mapa), e tratar duas
complicações: clustering (abrir popup exige `zoomToShowLayer`) e paginação server-side
(rolar até linha fora da página atual exige fetch-by-id ou índice global). Padrão de
referência já no código: `similarSeedId`. Escopo sugerido: MVP (foco na página atual +
pan/zoom) → fase 2 (cross-página + popup clusterizado).

---

### Follow-up Q&A (NEW — 2026-06-28)

**Q2:** tem uma questão de usabilidade também, o scroll faz o mapa desaparecer.
seria interessante se o scroll fosse só na Tabela.

**A2:** É um problema de layout, separado da sincronização. Em
`WorkspacePage.tsx:63` o grid de views usa `flex flex-1 overflow-auto` — esse
`overflow-auto` faz o **grid inteiro** rolar (mapa + tabela juntos), então o mapa
sai de vista quando a tabela cresce. A `TableView` já tem scroll interno próprio
(`TableView.tsx:281`, `flex-1 overflow-auto`), mas ele nunca atua porque o pai rola
primeiro. Correção: trocar o `overflow-auto` do grid por `overflow-hidden` (ou
`overflow-x-auto overflow-y-hidden` se quiser preservar scroll horizontal entre
muitas views). Assim cada view fica com altura fixa e rola seu próprio conteúdo; o
mapa fica parado. Atenção: com `overflow-hidden`, muitas views na horizontal se
espremem em vez de gerar scroll lateral — nesse caso use `overflow-x-auto
overflow-y-hidden` + `min-w` nos wrappers.

---

## Recommendations summary

1. **[HIGH]** Adicionar `activeReportId` + `setActiveReport` ao `workspaceStore`,
   ortogonal a `selectedIds`, espelhando o padrão `similarSeedId`.
2. **[HIGH]** Mapa→Tabela: `click` no `<Marker>` chama `setActiveReport`; `TableView`
   faz `scrollIntoView` + destaque (ring) na linha ativa, com fallback gracioso quando
   fora da página atual.
3. **[HIGH]** Tabela→Mapa: linha ativa chama `map.setView` para as coords; destaque
   visual do marcador.
4. **[MEDIUM]** Definir a semântica do clique na linha (foco vs. seleção da cesta) antes
   de implementar — mudança de comportamento atual.
5. **[MEDIUM]** Fase 2: `zoomToShowLayer` para abrir popup clusterizado; fetch-by-id /
   índice global para scroll cross-página.
6. **[LOW]** Confirmar se `MapView` deveria usar `allPoints: true` para que mapa e tabela
   exponham o mesmo universo de ids.
7. **[HIGH — quick win]** (follow-up) Corrigir o scroll: trocar `overflow-auto` por
   `overflow-hidden` no grid de views em `WorkspacePage.tsx:63` para que só a tabela role
   internamente e o mapa não desapareça. Fix isolado, 1 linha, independente da sync.
