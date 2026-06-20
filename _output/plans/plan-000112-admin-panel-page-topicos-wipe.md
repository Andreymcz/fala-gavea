# Plan 000112 | feat/admin-panel | 2026-06-20 20:37 UTC | Admin Panel page: seed topicos + wipe DB | Review: light
plan_format_version: 1
source: research-000110

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
- [ ] Done

### Step 2: Create `AdminPage.tsx`

Create `frontend/src/features/admin/AdminPage.tsx`.

**Seed topicos section** — file input (`accept=".csv"`) + submit button. On submit: call `api.seedTopicos(file)`, show result toast `"X tópicos inseridos, Y ignorados."` on success, error toast on failure. Show spinner while pending.

**Wipe database section** — two buttons: "Apagar relatos e encaminhamentos" and "Apagar tudo (incluindo tópicos)". Both open the same `ConfirmDialog` (built inline using the existing `Dialog` component from `@/components/ui/dialog`). The dialog body must repeat what will be deleted and require clicking "Confirmar" (not just dismiss). On confirm: call `api.wipeDatabase(includeReportTypes)`, show result toast `"Banco limpo: X relatos, Y encaminhamentos, Z tópicos."`, error toast on failure.

Layout pattern: same as `ForwardingsPage` — `flex flex-col p-6` with `h1` heading. Two visually separated card sections (bordered `div`s with padding) labeled "Seed de Tópicos" and "Limpar Banco de Dados".

- **Files**: `frontend/src/features/admin/AdminPage.tsx` (create)
- **Depends on**: Step 1
- **Verify**: page renders, CSV upload triggers `seedTopicos`, wipe buttons open confirm dialog and trigger `wipeDatabase`
- [ ] Done

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
- [ ] Done

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
- [ ] Done

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
