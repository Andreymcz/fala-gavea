# Plan 000158 | feat/anon-ux | 2026-06-24 00:26 UTC | Anonymous UX: toggle on report form, token storage, meus relatos | Review: light
plan_format_version: 1

source: roadmap-000151

## Brief

Add the anonymous submission toggle to `ReportFormPage`, store the returned claim token in localStorage, and add an anonymous "Meus relatos" path that lets citizens retrieve their own anonymous reports using the stored token.

## Context

Backend anonymous reporting is implemented in plan-000155. The frontend currently shows `ReportFormPage` at `/report` (requires auth). Anonymous submission allows unauthenticated users to report without creating an account. The backend returns a one-time UUID token in the POST /reports response; the frontend must store it and use it to retrieve anonymous reports via `GET /reports/mine?anonymous_token=`.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Token storage | `localStorage` key `fala_gavea_anon_token` | Persistent across sessions; survives page reload; mobile browser default |
| Anonymous vs. auth form | Same ReportFormPage, toggle at the top | Reduces surface area; single code path |
| ReportFormPage access | Allow unauthenticated when anonymous toggle is on | Remove RequireAuth guard for anonymous path |
| Post-submission feedback | Show token in a one-time dialog: "Guarde este código..." | User must see it before navigating away |
| "Meus relatos" anonymous tab | Added to WorkspacePage FilterPanel "Meus relatos" toggle logic | Reuses existing UI; checks both auth-based and token-based ownership |

## Steps

### Step 1: Anonymous toggle on ReportFormPage

In `frontend/src/pages/ReportFormPage.tsx`:

- Add a `Switch` at the top of the form: "Enviar sem identificação"
- Below the switch, show the copy: *"Ao enviar sem identificação, você receberá um código para acompanhar seu relato. Guarde esse código — sem ele não será possível acompanhar o andamento."*
- When the toggle is ON: set `anonymous: true` in the POST body; remove the `RequireAuth` gate for this form (the form page itself should be accessible without login when the toggle is on)
- When the toggle is OFF (default): require auth as before (show login prompt if no JWT)
- Pass `anonymous` flag in the `createReport` API call

Update `frontend/src/api/reports.ts`'s `createReport` function to accept `anonymous: boolean` and include it in the request body. The function does not need a token when `anonymous=true`.

- **Files**: `frontend/src/pages/ReportFormPage.tsx` (modify), `frontend/src/api/reports.ts` (modify)
- **Tests**: N/A
- [ ] Done

### Step 2: Token receipt and localStorage storage

After a successful anonymous submission, the POST /reports response includes `anonymous_claim_token: string`. In the form submission handler:

- If `anonymous_claim_token` is present in the response, show a modal/dialog:
  ```
  Seu relato foi enviado!
  Código de acompanhamento: [token]
  [Copiar código]   [Fechar]
  ```
- On "Copiar código": `navigator.clipboard.writeText(token)` + brief "Copiado!" confirmation
- On "Fechar" or after copy: store token in `localStorage.setItem('fala_gavea_anon_token', token)` (overwrite if exists — one token per browser)
- Navigate to `/` (workspace) after closing the dialog

- **Files**: `frontend/src/pages/ReportFormPage.tsx` (modify)
- **Verify**: Submitting anonymously shows the token dialog; token appears in localStorage after closing
- **Tests**: N/A
- [ ] Done

### Step 3: Anonymous "Meus relatos" in WorkspacePage

The existing "Meus relatos" toggle in `FilterPanel` sets `author_id = current_user.id` in `ReportFilters` and calls `POST /reports/query`. For anonymous users, this path is unavailable.

Add logic in `FilterPanel` (or in `useFilteredReports` hook):

- If `useAuth().user` is null (unauthenticated) AND `localStorage.getItem('fala_gavea_anon_token')` is non-null: show the "Meus relatos" toggle
- When the toggle is ON and user is unauthenticated: call `GET /reports/mine?anonymous_token=<stored_token>` instead of `POST /reports/query`
- Display the results in the existing table/map views (adapt the `items` shape from the mine endpoint to the `ReportResponse` format expected by the views)
- When toggle is OFF: show all public reports as normal

Add `getMyAnonymousReports(token: string)` to `frontend/src/api/reports.ts`.

- **Files**: `frontend/src/features/workspace/FilterPanel.tsx` (modify), `frontend/src/api/reports.ts` (modify)
- **Verify**: Unauthenticated user with a stored token sees their anonymous relato in "Meus relatos" toggle; no stored token → toggle is hidden
- **Tests**: N/A
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000158 (anon-ux)
