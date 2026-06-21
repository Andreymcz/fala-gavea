# QA Log — plan-000139 | Phase B: saved filters backend + UX | 2026-06-21 22:44 UTC

## Brief

Phase B Saved filters backend (domain port + SQLAlchemy repo + 5 use cases + CRUD router + Alembic migration) + saved filters UX (preset bar, save popover, load dropdown). FROM research 136

## Source plan

[plan-000139-phase-b-saved-filters-backend-ux.md](plan-000139-phase-b-saved-filters-backend-ux.md)

## Q&A

**Q1:** Why is no Alembic migration needed even though the brief mentions one?

**A1:** The project uses `Base.metadata.create_all()` in `create_tables()` which is called on every FastAPI startup (in `create_app()`). Adding `SavedFilterModel` to `models.py` is sufficient — the table is auto-created on next server start. Alembic is not installed or configured in the project. The brief's mention of "Alembic migration" was from the research-000136 spec template; the actual implementation uses the project's established pattern.

**Q2:** Why does `find_by_id` in the repository NOT filter by `owner_id`, while the use cases do?

**A2:** Repository methods are data-access primitives without business rules. Ownership enforcement is a domain/application concern, not a persistence concern. This keeps the repository testable in isolation (e.g., an admin use case in the future could legitimately look up any filter by id). The use cases (`GetSavedFilter`, `UpdateSavedFilter`, `DeleteSavedFilter`) perform the `sf.owner_id != owner_id → raise NotFoundError` check after `find_by_id` returns.

**Q3:** Why return 404 (not 403) when a filter belongs to another user?

**A3:** Per OWASP BOLA/IDOR prevention (research-000136 R9): returning 403 would confirm to an attacker that the resource exists, enabling enumeration. 404 gives nothing away — the resource "does not exist" from the requester's perspective. This is the standard pattern for private per-user resources in this codebase.

**Q4:** How does the Save popover decide whether to call `createSavedFilter` vs `updateSavedFilter`?

**A4:** When `loadedPresetId !== null` (a preset is loaded), the popover shows both "Salvar novo" and "Atualizar [name]" options. "Atualizar" calls `updateSavedFilter(loadedPresetId, { body: filters })`. "Salvar novo" always calls `createSavedFilter`. When no preset is loaded (`loadedPresetId === null`), only "Salvar" (create) appears.

**Q5:** The plan adds `loadedPresetId` to `workspaceStore` — why wasn't this in Phase A?

**A5:** Phase A had no saved-filter CRUD to call. `loadedPresetName` (string) was sufficient for display. Phase B needs the actual `id` to call `updateSavedFilter(id, ...)`. Adding `loadedPresetId: string | null` in Step 6 keeps the store extension minimal and adjacent to where it's consumed.
