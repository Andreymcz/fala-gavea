# Research 000129 | REDESIGN-X | 2026-06-21 16:33 | Refine data exploration search filters

tags: ux-patterns, filters, map, data-table, frontend-architecture, routing-bug

source: user request -- refine FilterPanel for citizen and public-agent exploration journeys

## User brief (verbatim)

> refine data exploration search filters in front end. citzen and public agent journeys.
>
> O painei laretal esquerdo e o coracao da busca. Precisamos refina-lo para comunicar claramente os filtros ativos, e adicionar um botao, para permitir que o usuario escreva e visualize os filtros e somente quando apertar o botao o filtro passa a ser ativo. quando apertar o botao o painel central e informato que o filtro mudou e precisa re-aplicar as mudancas.
>
> Pesquisar estrategias de visualizacao temporal tambem, ao inves de selecionar os dias nos calendarios, permitir escolher o intervalo de data de outras formas, exemplo: ultimos 15 dias.
>
> O combobox Tipos ( de relatos) no front nao esta mostrando os tipos disponiveis
>
> Feramenta tabela de relatos: nao tem como ver o texto do relato completo, nao pode ordenar
>
> MAPA: desenhar area nao esta funcionando direito, visualmente, trocar para opcao da ferramenta filtro para filtrar somente na area visivel no mapa

## Agent interpretation

Five refinements to the data-exploration workspace (left `FilterPanel` + central stacked views), shared by the citizen and public-agent journeys:

1. **Staged filter with Apply button.** The left panel is the heart of search. Refine it to clearly communicate which filters are active, and add a button so the user edits/previews filters as a *draft* and the filter only becomes active (and the central views re-fetch) when Apply is pressed.
2. **Temporal presets.** Replace bare date calendars with relative-range options like "ultimos 15 dias".
3. **Tipos combobox bug.** The report-type dropdown is empty in the deployed front.
4. **Table view gaps.** Cannot read the full report text (truncated) and cannot sort columns.
5. **Map area filter.** The two-click "Desenhar area" gives no visual feedback; switch to filtering by the currently visible map bounds.

## Files

- `frontend/src/features/workspace/FilterPanel.tsx` -- left panel, live filters, un-debounced semantic query
- `frontend/src/store/workspaceStore.ts` -- Zustand store, single `filters` object + `structuredFilters()` selector
- `frontend/src/hooks/useFilteredReports.ts`, `useSemanticSearch.ts` -- react-query, keyed on filters
- `frontend/src/features/workspace/views/MapView.tsx` -- `BboxDrawHandler` two-click draw, no rectangle feedback
- `frontend/src/features/workspace/views/TableView.tsx` -- text truncated to 80 chars, no sort
- `frontend/src/hooks/useReportTypes.ts`, `frontend/src/lib/api.ts` -- `GET /report_types` (slashless)
- `src/fala_gavea/presentation/api/routers/report_types.py`, `.../main.py` -- collection at `/`, SPA catch-all

---

## Findings

### F1 -- The "Apply button" request collides with a deliberate design intent (resolve in the user's favour, with eyes open)

`product-design-as-coded.md` records the workspace intent: *"the filter is yours and singular, and each view (map, table, topics, similars, chat) looks at the same set from different angles."* The current model is **live**: every `setFilter` merges into one `filters` object and all views re-read instantly.

The brief asks to replace this with a **staged** model (edit a draft, preview, then Apply). This is a legitimate product decision, but it changes the interaction contract, so it is worth being explicit:

- The performance argument for staging is **only partly true**. Type / Urgencia / Status are `<Select>` widgets that fire at most one change per decision -- they are cheap and are exactly the "live lens" the design was built around. The genuinely expensive input is the **semantic-search box** (`FilterPanel.tsx:121`): it calls `setSemanticQuery` on *every keystroke*, and `useSemanticSearch` has **no debounce**, so each character is an Ollama/Chroma round-trip.
- Therefore there are two coherent designs:
  - **(A) Full staged model + Apply** -- matches the brief literally; gives the "write, preview, then commit" control the user described and the explicit "filter changed, re-apply" signal to the centre.
  - **(B) Keep live filters, just debounce the semantic box (~350 ms) + add active-filter chips** -- lighter, preserves the design intent, fixes the only real perf problem, but does *not* give the explicit Apply gesture the user asked for.

Recommendation: **implement (A) because the user asked for it explicitly and wants the staged control**, but build it cleanly (see R1) and record (B) as the considered-and-deferred alternative so the team can revisit if users find live filtering more natural.

### F2 -- The Tipos combobox bug is a confirmed production routing defect (not a hypothesis)

`api.ts:121` calls `GET /report_types` (no trailing slash); the router exposes the collection at `@router.get("/")` under prefix `/report_types`, so the real route is `/report_types/`. Starlette would normally 307-redirect the slashless path -- **but** the SPA catch-all `@app.get("/{full_path:path}")` in `main.py:34` is matched first and returns `index.html`. The client then runs `res.json()` on HTML, the request throws, react-query falls back to `[]`, and the dropdown is silently empty.

Key detail: this is **invisible in `npm run dev`** (no `static/` dir, so the catch-all is not mounted and the 307 works) and **only bites in the FastAPI-served production build**. The same latent bug affects `GET /forwardings` (`api.ts:126`), which also calls a slashless collection route -- the agent journey's forwardings list is one build away from the same failure.

### F3 -- Temporal presets are a clean, low-risk win

Industry pattern is "presets + custom range": offer frequent relative ranges (Hoje, Ultimos 7/15/30 dias, Este mes) that compute `since`/`until`, with a "custom" path that reveals the existing date inputs. A documented UX caveat: relative ranges hide the actual dates, so **show the resolved absolute dates** next to the preset.

### F4 -- Table needs sort + a full-text escape hatch

`TableView.tsx:86` renders `p.text.slice(0, 80)` with no way to read the rest, and columns are not sortable. Both are standard data-table affordances. Client-side sort is fine at current scale; full text is best shown in a dialog (with focus management) or an expandable row.

### F5 -- The map "draw area" has no feedback; "filter this area" is simpler and more accessible

`BboxDrawHandler` requires two map clicks and renders **no rectangle**, so the user gets no answer to "what happened?". It is also a pointer-only gesture with no keyboard equivalent. A "Filtrar nesta area" button that reads `map.getBounds()` on demand is a single, labelable, keyboard-operable control -- a usability and accessibility improvement. (If free-draw is kept for power users, render a live `<Rectangle>` from corner-1 to the cursor.) Note bbox is already committed directly via `setBbox`, independent of the panel.

---

## Recommendations summary

| # | Recommendation | Priority |
|---|----------------|----------|
| R1 | **Staged filter model + Apply button** (per brief). Add a `draftFilters` slice alongside committed `filters` in `workspaceStore`; the FilterPanel edits the draft; an **Aplicar** button commits draft -> filters (views re-fetch only then); keep **Limpar**. Show a **dirty indicator** ("filtros alterados -- clique Aplicar") and **active-filter chips** summarising committed filters with per-chip remove. Decide map/table interactions explicitly: **map-drawn bbox and table "Similares" commit immediately** (direct manipulation), only panel fields are staged. Wire `aria-live` for the dirty indicator and chip add/remove. | HIGH |
| R2 | **Fix the Tipos (and latent Forwardings) routing bug.** Centralised fix: guard the SPA catch-all in `main.py` so it returns 404 / falls through for known API prefixes (`auth`, `nl`, `reports`, `report_types`, `forwardings`, `admin`, `health`); also align `api.ts` to call the canonical trailing-slash collection routes. Add a backend test asserting `GET /report_types` returns `application/json` and a frontend test that the combobox populates. | HIGH |
| R3 | **Temporal presets.** Add relative-range presets (Hoje, Ultimos 7/15/30 dias, Este mes, Personalizado) that compute `since`/`until`; reveal the native date inputs only for "Personalizado"; display the resolved absolute dates. Keep native `<input type="date">` for keyboard/locale safety. | MEDIUM |
| R4 | **Table sort + full text.** Add client-side column sorting (Texto, Tipo, Urgencia, Status, Data) with header affordances, and a full-text reader (dialog with focus in/out + Esc, or expandable row). | MEDIUM |
| R5 | **Map "Filtrar nesta area".** Replace/augment the two-click draw with a button that sets bbox to `map.getBounds()`; if draw is retained, render a live `<Rectangle>` for feedback; keep "Limpar area". | MEDIUM |
| R6 | **Regression tests** for R2 (backend content-type + frontend combobox) -- the current suite catches neither, which is why the bug shipped. | LOW |

**Considered & deferred alternative to R1:** keep live filters and instead debounce the semantic-search box (~350 ms) + add active-filter chips. Lighter and preserves the "live lens" intent, but does not provide the explicit Apply gesture the brief requested. Regardless of R1, **debounce the semantic box** -- it is the one real per-keystroke load and should not stay un-throttled.

---

## Q&A log

**Q1 (initial):** Refine the left-panel data-exploration filters: add a staged Apply button that communicates active filters; research temporal-range strategies (e.g. "ultimos 15 dias"); fix the empty Tipos combobox; add full-text + sorting to the reports table; and replace the broken map draw-area with a filter-by-visible-area tool.

**A1:** Five recommendations (R1-R6 above). The Apply button is implementable as a draft+committed Zustand model and is honoured per the explicit brief, with the caveat that it diverges from the documented "single live filter" intent -- the lighter alternative is debouncing only the semantic box plus active-filter chips. The Tipos combobox is a confirmed production-only routing bug: the slashless `GET /report_types` is swallowed by the SPA catch-all and returns HTML; the same defect is latent for `GET /forwardings`. Temporal presets, table sort/full-text, and the map "search this area" pattern are standard, well-supported UX improvements. Debounce the semantic search regardless.

## Sources

- [Filter UX Design Patterns & Best Practices -- Pencil & Paper](https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-filtering)
- [Search Filters: 5 best practices for a great UX -- Algolia](https://www.algolia.com/blog/ux/search-filter-ux-best-practices)
- [The Most Popular Date Filter UI Patterns -- Evolving Web](https://evolvingweb.com/blog/most-popular-date-filter-ui-patterns-and-how-decide-each-one)
- [Fix the UX Gap: Dynamic Date Ranges for Relative Filters -- Medium](https://ramdosk92.medium.com/fix-the-ux-gap-how-to-display-dynamic-date-ranges-for-relative-filters-in-crm-analytics-dashboard-41e92f1226b5)
- [Search this area -- Map UI Patterns](https://mapuipatterns.com/search-this-area/)
