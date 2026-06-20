# QA Log | plan-000112 | 2026-06-20 20:39 UTC | Admin Panel page: seed topicos + wipe DB

## Brief

Admin Panel page (CSV upload for topicos, wipe with confirmation dialog, route /admin guarded by admin role)

## Q&A

**Q:** Plan an Admin Panel page (CSV upload for topicos, wipe with confirmation dialog, route /admin guarded by admin role)

**A:** Plan 000112 created. Four steps:
1. Add `seedTopicos(file)` and `wipeDatabase(includeReportTypes)` to `api.ts`
2. Create `frontend/src/features/admin/AdminPage.tsx` with CSV upload section and wipe section (confirmation dialog using existing Dialog component)
3. Register `/admin` route in `App.tsx` guarded by `RequireAuth roles={["admin"]}`
4. Add "Painel admin" header link visible only to admin role

Key design decision: `seedTopicos` uses raw `fetch` (not shared `request()`) to avoid corrupting multipart/form-data boundary.
