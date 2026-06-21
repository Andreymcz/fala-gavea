# Research 000136 | REDESIGN-X | 2026-06-21 19:40 UTC | Left panel search engine: filter UI, NL chat, saved filters, table UX

tags: ux-patterns, filters, nl-to-filter, saved-filters, table, left-panel, llm-structured-output, api-design, security

source: user request — left panel as core UI of the search engine, NL chat for filter intent, saved/loaded named filters, table visualization improvements. Layered on research-000129/000130 and plan-000131/000132.

---

## User brief (verbatim)

> left panel as core UI of search engine: it show the data filtering possibilities and current active filters. An Active filter has a name and can be loaded and saved. an small, on left pannel, chat allow the user to write filter intentions. the chat sugest a filter params that the user can review and apply in current UI. The user can name and save a filter easely. also review the plans and researchers linked in this conversation in order to create a better table visualization and experience on main panel

## Agent interpretation

This research designs the **complete left panel + table surface** for the workspace, building on what already exists:

- **DONE (plan-000132):** `POST /reports/query` — unified endpoint combining multi-value structured filters, bbox, date range, text LIKE, semantic ranker, pagination. `useFilteredReports` already consumes it.
- **PENDING (plan-000131):** staged draft/Apply model, active-filter chips, date presets, TableView column sort + full-text dialog, MapView "Filtrar nesta área", SPA routing fix.
- **NOT YET DESIGNED (this research — 000136):** named active filters, save/load filter presets (Phase C from research-000130), NL-to-filter chat assistant (Phase A), and a more complete table UX.

**Four capabilities being jointly designed:**
1. **Left panel layout** — the single scrollable rail that is the heart of the search engine. Must communicate: available filter dimensions, currently committed filters (named, removable chips), staged-but-not-yet-applied draft state, and controls for saving/loading a filter preset.
2. **NL-to-filter chat** (compact, within the panel). A small input where the user writes in natural language; Ollama `qwen3:8b` returns a validated `ReportQueryBody` subset that populates the draft chips. Never auto-applies. New backend endpoint: `POST /nl/filter`.
3. **Saved filters** (Phase C). Per-user private named blobs. Save the current committed filter state with a name; load it later (populates draft → user applies). New backend: `saved_filters` table + CRUD endpoints.
4. **Table visualization improvements** — client-side sort, full-text reader (Radix Dialog), pagination driven by `total` from the API envelope, score column when `ranked_by="similarity"`.

## Files

- `frontend/src/features/workspace/FilterPanel.tsx` (current: 130 lines, live, no staging, `w-56`)
- `frontend/src/store/workspaceStore.ts` (current: single `filters`, no `draftFilters`)
- `frontend/src/features/workspace/views/TableView.tsx` (current: `p.text.slice(0, 80)`, no sort, no pagination)
- `frontend/src/lib/types.ts` (`WorkspaceFilters`, `ReportQueryBody`, `ReportQueryResponse`)
- `frontend/src/lib/api.ts` (`queryReports`)
- `src/fala_gavea/domain/repositories/semantic_ports.py` (ports: `IReportIndexer`, `ISemanticSearchPort`, `ILLMClient`)
- `src/fala_gavea/presentation/api/routers/chat.py` (pattern to mirror for `POST /nl/filter`)
- `src/fala_gavea/infrastructure/ollama/ollama_client.py` (LLM calls)
- `src/fala_gavea/application/use_cases/chat/answer_with_rag.py` (pattern for new use case)
- `src/fala_gavea/domain/repositories/` (new: `ISavedFilterRepository`, `IFilterParser`)
- `src/fala_gavea/infrastructure/repositories/` (new: `SQLAlchemySavedFilterRepository`)
- `src/fala_gavea/infrastructure/database/models.py` (new: `SavedFilterModel`)
- `src/fala_gavea/presentation/api/routers/nl.py` (extend with `/filter`)
- New: `src/fala_gavea/presentation/api/routers/saved_filters.py`

---

## Findings

### F1 — Left panel spatial layout: four named sections, `w-72`, collapsible

The current panel is `w-56` (224 px). With named filter preset controls, active-filter chips, dirty indicator, draft filter selects, date presets, and an NL input, 224 px causes overflow at real content lengths ("Tipo: Iluminação pública" alone is ~170 px at text-xs). **Recommended minimum width: `w-72` (288 px).** Add a collapse toggle (icon button pinned to the right edge) that sets `panelOpen: boolean` in `workspaceStore`; when collapsed, show only the toggle with a chip-count badge for quick status awareness. This preserves map/table space on smaller viewports.

**Four-section ordering (top → bottom in the scrollable rail):**

| Section | Purpose | Fixed/scrolls |
|---|---|---|
| 1 — Preset bar | Current filter name (or "Sem nome"), Save button, Load dropdown | Fixed header |
| 2 — Active chips | Committed filter chips (removable ×), chip count, "Nenhum filtro ativo" empty state | Scrollable, max-height ~80 px |
| 3 — Draft controls | Filter selects, date presets, text/bbox inputs, Apply + Limpar buttons, dirty indicator | Scrollable main area |
| 4 — NL assistant | Compact textarea + Send button; inline chip preview below | Fixed footer |

This ordering puts the most stable information (what's currently active) near the top for immediate visibility, the editing surface in the middle, and the conversational assistant at the bottom as an enhancement layer.

### F2 — Staged draft + Apply model (extending plan-000131)

Plan-000131 already designs this (Step 1 of plan-000131). The key additions from this research:
- **`panelOpen: boolean`** in store (new)
- **`draftFilterName: string`** in store — the name the user has typed for the current draft (distinct from the loaded preset name)
- **`loadedPresetName: string | null`** in store — the name of the preset currently loaded (shown in Section 1 header; cleared when the user modifies the draft)
- **Draft loss guard**: if `isDirty()` and user navigates (SPA route change), show a Radix `AlertDialog` — "Você tem filtros não aplicados. Deseja descartá-los?" This prevents the **IIa2 ("What happened?")** communicability breakdown.

The NL chat populates the draft identically to manual edits. The Apply gesture is the single commit point regardless of how the draft was composed.

### F3 — NL-to-filter chat: compact, role-separated, validate before populating

The existing conversational chat (POST /nl/chat, plan-000100) is full RAG — multi-turn, agent+admin only. The filter-parse assistant is different in kind:
- **Single-turn, not conversational.** User types one natural language query; LLM returns a structured filter JSON; chips appear in the draft panel. The user then presses Apply or adjusts.
- **All roles.** Filtering is not sensitive; all authenticated users (citizen, agent, admin) should be able to use NL filter intent. No role restriction beyond `get_current_user`.
- **Transparency contract:** the parsed chips must show exactly what was understood. If the LLM returns `urgency: "urgente"` (invalid), the validator drops it and shows a note: "Não entendi: urgência 'urgente' não é válida." Never silently coerce.
- **Single repair retry:** on first Pydantic parse failure, send the raw LLM output back in a correction prompt: "This JSON was invalid. Fix it to match the schema." On second failure, return `{"error": "parse_failed", "partial": {...valid fields only...}}`. The frontend shows partial chips + "O assistente não conseguiu interpretar todos os filtros — revise manualmente."
- **Graceful 503:** Ollama unavailable → 503 `{"detail": "llm_timeout"}`. Frontend shows "O assistente de filtros está indisponível — use os controles manuais." The manual filter controls are always visible and functional. Never block manual usage on LLM availability.
- **Prompt injection mitigation:** use Ollama `format` parameter (JSON schema-guided decoding) so the model output channel is structurally restricted to the filter JSON schema. The system prompt and user content are role-separated (system = instructions + schema, user = typed text). The parsed result flows through Pydantic before touching the frontend.

**NL input placement:** fixed-footer Section 4, as described in F1. A small `<Textarea rows={2}>` with placeholder "Descreva o filtro em linguagem natural..." and a Send (→) icon button. Loading state: spinner replaces the Send icon; textarea disabled. Error state: inline alert below the textarea with the error reason. Parsed chips appear in a light-blue preview zone ("Sugestão do assistente") below the textarea, with an "Aplicar sugestão ao rascunho" button (merges into `draftFilters`) and a "Descartar" button.

### F4 — Saved filters: named blobs, per-user, load into draft

**UX flow:**
1. **Save:** user presses "Salvar" (Section 1). If no name is set, a popover/inline input appears: "Nome do filtro:" with a text field and "Confirmar" button. On confirm, `POST /saved-filters` with `{name, body: currentCommittedFilters}`.
2. **Load:** user opens the "Carregar" dropdown (Section 1). Shows list of their saved filters by name, most recent first. On select: `GET /saved-filters/{id}` → validate → populate `draftFilters` → set `loadedPresetName`. User sees the loaded filter name in the header and the loaded chips in Section 2 (via Apply). One step: user presses Apply and the preset becomes active.
3. **Delete:** each item in the load dropdown has a trash icon. Confirmation in a tooltip or popover before `DELETE /saved-filters/{id}`.
4. **Auto-naming fallback:** if the user clicks Save without typing a name and dismisses the input, auto-name from chip summary: "Alta, últimos 30 dias, Iluminação" (truncated to 40 chars). This removes friction for quick saves.

**Filter name in the header:** always visible in Section 1 — "Sem nome" when no preset is active, the preset name when one is loaded, and the preset name + asterisk when a loaded preset has been modified (draft differs from the loaded body). This gives continuous feedback on "where am I relative to my saved filters."

### F5 — Saved filters backend: SQLite blob + ownership enforcement

**Schema:**
```sql
CREATE TABLE saved_filters (
  id         TEXT PRIMARY KEY,              -- UUID4
  owner_id   TEXT NOT NULL REFERENCES users(id),
  name       TEXT NOT NULL,
  body       TEXT NOT NULL,                -- JSON: ReportQueryBody subset
  schema_ver TEXT NOT NULL DEFAULT '1',   -- for future migration
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX idx_sf_owner ON saved_filters(owner_id);
```

**Endpoints:**
```
POST   /saved-filters         → 201, SavedFilterResponse (create)
GET    /saved-filters         → 200, list[SavedFilterResponse] (list own)
GET    /saved-filters/{id}    → 200 | 404 (read own; 404 if not owner)
PATCH  /saved-filters/{id}    → 200 (update name or body)
DELETE /saved-filters/{id}    → 204 (delete own)
```

All endpoints require `get_current_user` (any role). Every SQL query includes `WHERE owner_id = current_user.id` — **not derived from the request body**. Return `404` (not `403`) when a filter exists but belongs to another user: 403 would confirm resource existence, a BOLA disclosure.

**On load:** deserialize `body` JSON through the current `ReportQueryBody` Pydantic schema. Fields that no longer exist in the schema are silently dropped; a deprecation note is appended to the response if any fields were dropped (`deprecated_fields: ["old_field"]`). Never return a 422 on a stale saved filter — graceful degradation only.

**Clean-architecture layering:**
- `domain/repositories/saved_filter_repository.py` → `ISavedFilterRepository` ABC (methods: `save`, `get`, `list_for_user`, `update`, `delete`)
- `domain/entities/saved_filter.py` → `SavedFilter` dataclass
- `infrastructure/repositories/sqlalchemy_saved_filter_repository.py` → SQLAlchemy implementation
- `infrastructure/database/models.py` → `SavedFilterModel`
- `application/use_cases/saved_filters/` → `CreateSavedFilter`, `ListSavedFilters`, `GetSavedFilter`, `UpdateSavedFilter`, `DeleteSavedFilter`
- `presentation/api/routers/saved_filters.py` → FastAPI router
- `presentation/schemas/saved_filter.py` → Pydantic request/response schemas

### F6 — NL filter parser backend: `POST /nl/filter`, `IFilterParser` port

**New port** in `domain/repositories/filter_ports.py` (or add to `semantic_ports.py`):
```python
class IFilterParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> dict[str, Any]:
        """Return a ReportQueryBody-compatible dict. May raise ParseError."""
```

**Infrastructure implementation** in `infrastructure/ollama/filter_parser.py`:
- Wraps `OllamaClient` (or the existing LLM factory for provider agnosticism)
- Sends: `system` = schema + instructions, `user` = typed text
- Uses Ollama `format` param with the JSON schema of `ReportQueryBody` subset (`report_type_ids`, `urgencies`, `statuses`, `since`, `until`, `text`, `q`) to constrain output
- Parse → Pydantic → on failure, one repair retry → on second failure, `ParseError(partial_dict, raw_output)`

**Use case** in `application/use_cases/nl/parse_nl_filter.py`:
```
ParseNLFilter(filter_parser: IFilterParser | None)
  .execute(text: str) -> ParseNLFilterResult(body: ReportQueryBody, warnings: list[str])
```

**Router extension** — add to `src/fala_gavea/presentation/api/routers/nl.py`:
```
POST /nl/filter  (any authenticated user)
  body: {text: str}
  response: {body: ReportQueryBody, warnings: list[str]} | 503 | 429
```

**Timeout:** 8 seconds hard timeout on the Ollama HTTP call. The `OllamaClient` (or `httpx.AsyncClient`) must declare this. On `TimeoutException`: `raise HTTPException(503, "llm_timeout")`. The existing `ollama_client.py` uses `requests`; this endpoint should use async to avoid blocking the FastAPI worker.

**Rate limiting:** `slowapi` (or a simple in-process counter dict) — `10 req/minute` per `current_user.id`. Return `429 {"detail": "rate_limit_exceeded", "retry_after": 60}`. This is the sole defense against Ollama saturation until usage patterns are measured.

### F7 — Table visualization improvements

**Column sort:** use TanStack Table v8 (`@tanstack/react-table`) if not already installed, or implement manually with a `sortConfig: {key: string, dir: 'asc'|'desc'} | null` state in the `TableView` component (local state, not store). Sort is **client-side over the currently loaded page** — not a new API call. Sortable columns: Tipo, Urgência, Status, Data, Relevância (score). Sort icon: `↑`/`↓` on active column, `⇅` on others. Keyboard-accessible via `onClick` and `onKeyDown` on `<th>`.

**Full-text reader:** `Radix Dialog` (not an expandable row). Trigger: "Ler relato" link/button in the text cell (replacing the current 80-char truncation). Dialog content: full text, Tipo, Urgência, Status, Data, lat/lon, and a "Similares" button (calls `setSimilarSeed`). Focus trapped inside, `Escape` closes, focus returns to the triggering row. Expandable rows were considered and rejected: in a dense table with pagination, expanding a row shifts layout unpredictably.

**Pagination:** the API returns `{items, total, limit, offset, ranked_by}`. Add `page: number` to local state (not store). Controls: `< Anterior | Página N de M | Próxima >` bar below the table. On page change: update the `offset` in `useFilteredReports` body and let react-query re-fetch. Default `limit: 50` (up from current 200 limit with no pagination). Show "N relatos encontrados, página X de Y" as a caption above the table header.

**Score column:** only visible when `data.ranked_by === "similarity"`. Column header: "Relevância" with a tooltip icon explaining "Pontuação de similaridade semântica". Cell: 0.00–1.00 formatted to 2 decimal places. Color-coded: ≥0.7 green, 0.4–0.7 amber, <0.4 gray. This makes the semantic-ranking behavior legible without requiring user knowledge of cosine similarity.

**Row density:** add a small density toggle (compact / confortável) as a toolbar icon above the table. Affects `TableRow` className padding. Compact is useful for agents reviewing large sets; comfortable for readable text.

---

## Recommendations summary

| # | Recommendation | Priority |
|---|----------------|----------|
| R1 | **Four-section left panel at `w-72` with collapse toggle.** Sections: Preset bar (fixed header), Active chips (scrollable, max-height ~80 px), Draft controls (main scrollable area), NL assistant (fixed footer). Width `w-72`; `panelOpen` boolean in store. | HIGH |
| R2 | **Extend plan-000131's draft model with `loadedPresetName`, `draftFilterName`, and a draft-loss guard.** When `isDirty()` and the user navigates, show a Radix AlertDialog. Show the preset name + `*` in the Section 1 header when the loaded preset has been modified. | HIGH |
| R3 | **NL filter parser: `POST /nl/filter` (any authenticated user).** LLM returns structured JSON via Ollama `format` parameter; Pydantic-validate; one repair retry; 503 on timeout/unavailable; partial results on second failure. Parsed chips appear in a "Sugestão do assistente" preview zone (Section 4); user presses "Aplicar sugestão" to merge into draft. Never auto-apply. | HIGH |
| R4 | **Saved filters backend:** `ISavedFilterRepository` port, SQLite `saved_filters` table (UUID id, `owner_id FK`, `name`, `body JSON`, `schema_ver`, timestamps), CRUD endpoints at `/saved-filters`. Ownership enforced server-side; `GET/PATCH/DELETE` with non-owner → 404 (not 403). Validate body on load; drop stale fields gracefully. | HIGH |
| R5 | **`IFilterParser` port in `domain/` + `OllamaFilterParser` in `infrastructure/ollama/`.** Use case `ParseNLFilter` owns retry + fallback. 8-second Ollama timeout. Rate limit: `10 req/min` per user. | HIGH |
| R6 | **Saved filters UX:** Section 1 preset bar — name display, Save popover (with auto-name fallback), Load dropdown (name + trash per item). On load: populate `draftFilters` + set `loadedPresetName`; user applies. Show `*` on header when loaded preset is dirty. | MEDIUM |
| R7 | **TableView: client-side column sort (Tipo, Urgência, Status, Data, Relevância), Radix Dialog for full text, pagination controls (`limit: 50`, `< N de M >` bar), score column conditional on `ranked_by="similarity"`, density toggle.** | MEDIUM |
| R8 | **NL assistant graceful degradation:** when 503, show "O assistente de filtros está indisponível — use os controles manuais" in Section 4; manual controls remain fully usable. Never show a blank/broken state for the whole panel on LLM failure. | MEDIUM |
| R9 | **BOLA prevention on saved-filter CRUD:** `WHERE owner_id = current_user.id` in every SQL query. Return 404 (not 403) on non-owned resource access. Never derive ownership from the request body. | HIGH (security) |

**Phasing (recommended build order):**
1. **Phase A (plan-000131 extended):** Four-section panel layout, `w-72`, collapse toggle, draft model with `loadedPresetName`/`draftFilterName`, date presets, active chips, Apply/Limpar, dirty indicator, draft-loss guard. Table sort, full-text dialog, pagination. SPA routing fix. This is plan-000131 expanded.
2. **Phase B (new plan):** Saved filters backend (domain port + SQLAlchemy repo + 5 use cases + CRUD router + Alembic migration) + saved filters UX (preset bar, save popover, load dropdown).
3. **Phase C (new plan):** NL filter parser backend (`IFilterParser` port + `OllamaFilterParser` + `ParseNLFilter` use case + `POST /nl/filter` endpoint) + NL assistant UX (Section 4 input, suggestion preview zone, "Aplicar sugestão" button).

**Considered and rejected:**
- *Inline row expansion for full text* — rejected due to unpredictable layout shift in a paginated table.
- *Auto-applying NL suggestions* — rejected: silent wrong filter is a worse failure mode than one extra button press.
- *Pushing saved-filter body to Chroma for semantic search* — out of scope; the filter body is a query, not a document.
- *Sharing saved filters across users* — deferred; per-user private is the PoC scope. BOLA risk would increase significantly with shared filters.
- *Persistent rate limiting via Redis* — overkill for Railway/PoC; in-memory `slowapi` is sufficient.

---

## Q&A log

**Q1 (initial):** Design the left panel as the core search engine UI: filter visualization, active filter chips with names, NL chat assistant that suggests filter params into the draft, save/load named filters, and a better table visualization on the main panel. Build on research-000129/000130 and plan-000131/000132.

**A1:** Nine recommendations (R1-R9). The left panel is redesigned as a four-section scrollable rail at `w-72` with a collapse toggle: (1) preset bar showing the current filter name and save/load controls, (2) active-filter chips (committed, removable), (3) draft filter controls (selects, date presets, Apply/Limpar, dirty indicator), and (4) a compact NL assistant at the bottom. The NL assistant (`POST /nl/filter`) parses natural language into a structured draft via Ollama `qwen3:8b` with JSON-schema-guided output, Pydantic validation, one repair retry, and a graceful 503 fallback — suggestions appear as a chip preview for user review before Apply. Saved filters are per-user private SQLite blobs with a `ISavedFilterRepository` domain port, full CRUD, server-side ownership enforcement (WHERE owner_id = current_user.id; 404 on non-owned), and stale-field validation on load. The table gets client-side sort, a Radix Dialog for full text, pagination driven by the API `total`, a conditional score column, and a density toggle. Build order: Phase A = extended plan-000131 (layout + draft model + table); Phase B = saved filters; Phase C = NL parser.

## Sources

- [Algolia Filter UX Best Practices](https://www.algolia.com/blog/ux/search-filter-ux-best-practices)
- [Radix UI Dialog](https://www.radix-ui.com/primitives/docs/components/dialog)
- [TanStack Table v8 sorting](https://tanstack.com/table/v8/docs/guide/sorting)
- [Ollama structured output / format parameter](https://ollama.com/blog/structured-outputs)
- [slowapi rate limiting for FastAPI](https://github.com/laurents/slowapi)
- [OWASP BOLA/IDOR prevention](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- research-000129: Refine data exploration search filters
- research-000130: Filter assistant NL to query params + unified query API
- plan-000131: Refine data exploration search filters (PENDING)
- plan-000132: Unified reports query API Phase B (DONE)
