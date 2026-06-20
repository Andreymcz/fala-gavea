# DONE | 2026-06-20 21:21 UTC | Plan 000112 | feat/admin-panel | 2026-06-20 20:37 UTC | Admin Panel page: seed topicos + wipe DB | Review: light
plan_format_version: 1
source: research-000110
spawned: plan-000113

## Context

Feature 109 (plan-000109) added three backend-only admin operations accessible via Swagger UI/curl only:
- `POST /admin/seed/topicos` — CSV bulk-create ReportTypes
- `DELETE /admin/seed/wipe` — wipe all reports/forwardings (+ optional report_types)

This plan adds a minimal React Admin Panel page at `/admin`, guarded by `RequireAuth roles={["admin"]}`, exposing both operations through a simple UI.

## Steps

### Step 1: Add admin API methods to `api.ts`

Add two methods to `frontend/src/lib/api.ts`:

```ts
seedTopicos(file: File): Promise<{ inserted: number; skipped: number; errors: unknown[] }> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const formData = new FormData();
  formData.append("file", file);
  return fetch(`${BASE_URL}/admin/seed/topicos`, { method: "POST", headers, body: formData })
    .then(async (res) => {
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: res.statusText }));
        throw new ApiError(res.status, data.detail || res.statusText);
      }
      return res.json();
    });
},

wipeDatabase(includeReportTypes: boolean): Promise<{ wiped: { reports: number; forwardings: number; report_types: number } }> {
  return request("DELETE", `/admin/seed/wipe?include_report_types=${includeReportTypes}`);
},
```

Note: `seedTopicos` cannot use the shared `request()` helper because it sends `multipart/form-data` (browser sets the boundary automatically when using `FormData` directly — setting `Content-Type` manually would break it).

- **Files**: `frontend/src/lib/api.ts` (modify)
- **Verify**: TypeScript compiles; no import changes needed
- [x] Done

### Step 2: Create `AdminPage.tsx`

Create `frontend/src/features/admin/AdminPage.tsx`.

**Seed topicos section** — file input (`accept=".csv"`) + submit button. On submit: call `api.seedTopicos(file)`, show result toast `"X tópicos inseridos, Y ignorados."` on success, error toast on failure. Show spinner while pending.

**Wipe database section** — two buttons: "Apagar relatos e encaminhamentos" and "Apagar tudo (incluindo tópicos)". Both open the same `ConfirmDialog` (built inline using the existing `Dialog` component from `@/components/ui/dialog`). The dialog body must repeat what will be deleted and require clicking "Confirmar" (not just dismiss). On confirm: call `api.wipeDatabase(includeReportTypes)`, show result toast `"Banco limpo: X relatos, Y encaminhamentos, Z tópicos."`, error toast on failure.

Layout pattern: same as `ForwardingsPage` — `flex flex-col p-6` with `h1` heading. Two visually separated card sections (bordered `div`s with padding) labeled "Seed de Tópicos" and "Limpar Banco de Dados".

- **Files**: `frontend/src/features/admin/AdminPage.tsx` (create)
- **Depends on**: Step 1
- **Verify**: page renders, CSV upload triggers `seedTopicos`, wipe buttons open confirm dialog and trigger `wipeDatabase`
- [x] Done

### Step 3: Register route `/admin` in `App.tsx`

Add a lazy import and route:

```tsx
const AdminPage = lazy(() => import("@/features/admin/AdminPage").then(m => ({ default: m.AdminPage })));
```

```tsx
<Route
  path="/admin"
  element={
    <RequireAuth roles={["admin"]}>
      <Suspense fallback={<LoadingFallback />}>
        <AdminPage />
      </Suspense>
    </RequireAuth>
  }
/>
```

- **Files**: `frontend/src/App.tsx` (modify)
- **Depends on**: Step 2
- **Verify**: navigating to `/admin` as non-admin redirects to `/`; as admin renders the page
- [x] Done

### Step 4: Add "Painel admin" link to `Header.tsx`

Add a link visible only when `user.role === "admin"`, alongside the existing agent/admin "Encaminhamentos" link:

```tsx
{user?.role === "admin" && (
  <Link to="/admin" className="text-sm text-gray-600 hover:text-gray-900">
    Painel admin
  </Link>
)}
```

- **Files**: `frontend/src/components/layout/Header.tsx` (modify)
- **Depends on**: Step 3
- **Verify**: admin user sees "Painel admin" in header; agent and citizen do not
- [x] Done

## Review

**Depth: light** (auto=light, floor=light, flag=none)

| Perspective | Finding | Status |
|---|---|---|
| P1 Security | Route guarded by `RequireAuth roles={["admin"]}` — non-admins redirected client-side; backend enforces 403 independently | Adopted |
| P1 Security | Wipe action requires explicit confirm dialog — no accidental single-click data loss | Adopted |
| P0 Correctness | `seedTopicos` uses raw `fetch` + manual `FormData` to avoid corrupting multipart boundary (cannot use shared `request()` helper for file uploads) | Adopted |
| P2 Simplicity | Dialog reuses existing `@/components/ui/dialog` — no new UI primitives | Adopted |
| P2 Simplicity | "Painel admin" header link visible only to `role === "admin"` (not agent) — admin-specific tooling | Adopted |

## Commit

```
feat(admin-panel): admin page — seed topicos CSV + wipe DB with confirm dialog
```

## Implementation Summary

Mode: manual (4 sequential steps). All 4 steps completed.

**Files changed:**
- `frontend/src/lib/api.ts` (modify) — added `seedTopicos(file)` (raw `fetch` + `FormData` multipart, Bearer header) and `wipeDatabase(includeReportTypes)` (shared `request()` DELETE with query param). Response types mirror backend `SeedTopicosResponse` / `WipeResponse`.
- `frontend/src/features/admin/AdminPage.tsx` (create) — `/admin` page with two card sections: "Seed de Tópicos" (CSV file input + submit, spinner, result/error toasts) and "Limpar Banco de Dados" (two destructive buttons opening a shared confirm `Dialog`; wipe only fires on "Confirmar"). Scope state distinguishes reports-only vs. include-report_types.
- `frontend/src/features/admin/AdminPage.test.tsx` (create) — 3 vitest cases: renders both sections, CSV upload calls `seedTopicos(file)`, confirm-dialog gating (wipe not called until "Confirmar", then called with `true`).
- `frontend/src/App.tsx` (modify) — lazy `AdminPage` import + `/admin` route guarded by `RequireAuth roles={["admin"]}`.
- `frontend/src/components/layout/Header.tsx` (modify) — "Painel admin" nav link shown only when `user?.role === "admin"`.

**Quality gate:**
- TypeScript `tsc --noEmit`: clean.
- Vitest: 31 passing (28 prior + 3 new admin tests).
- ESLint on changed files: clean (3 repo-wide pre-existing errors live in untouched files).
- Project validation (`run_all_checks.py`): no new failures attributable to this change. `check_unused_files.py` flags `AdminPage.tsx` — confirmed pre-existing false positive: the checker doesn't follow dynamic `import()`, so every lazy-loaded page (WorkspacePage, ForwardingsPage, Login/Register, ReportForm) is flagged identically.
- Review (light depth, inline): all plan-adopted perspectives verified (admin route guard + independent backend 403, confirm-dialog wipe gate, multipart-boundary-safe upload, primitive reuse).

**Deferred / notes:**
- `seedTopicos` raw `fetch` does not dispatch `auth:unauthorized` on 401 (the shared `request()` helper does). Non-blocking; matches the plan's specified code; acceptable for an admin-only tool.
