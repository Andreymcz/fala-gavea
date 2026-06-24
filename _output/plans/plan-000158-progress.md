# plan-000158-progress

## 2026-06-24 — Implementation complete

### Steps completed

**Step 1 — Anonymous toggle on ReportFormPage**: Done
- Added `anonymous?: boolean` to `CreateReportBody` in `frontend/src/lib/types.ts`
- Added `anonymous_claim_token?: string | null` to `ReportDetail` in `frontend/src/lib/types.ts`
- Rewrote `frontend/src/features/report/ReportFormPage.tsx`:
  - Added checkbox-styled toggle "Enviar sem identificação"
  - When `anonymous=false` and user is not logged in: shows a login prompt with link + toggle to switch to anonymous
  - When `anonymous=true`: toggle is visible and advisory text shown
  - Removed `<RequireAuth>` from `/report` route in `frontend/src/App.tsx`
  - Pass `anonymous: true` in `createReport` body when toggle is on

**Step 2 — Token receipt and localStorage storage**: Done
- On successful anonymous submission with `anonymous_claim_token` in response: shows Dialog
- Dialog has the claim token, "Copiar código" button with "Copiado!" feedback, and "Fechar" button
- "Fechar" stores token to `localStorage['fala_gavea_anon_token']` and navigates to "/"
- For non-anonymous responses (or when not anonymous): existing toast + navigate flow preserved

**Step 3 — Anonymous "Meus relatos" in WorkspacePage**: Done
- Added `getMyAnonymousReports(token)` to `frontend/src/lib/api.ts` calling `GET /reports/mine?anonymous_token=<token>` (public endpoint)
- Introduced `ANON_AUTHOR_SENTINEL = '__anon__'` in `frontend/src/hooks/useFilteredReports.ts`
- Modified `useFilteredReports` to detect sentinel, run `getMyAnonymousReports` query instead of normal `queryReports`, and convert `ReportDetail[]` to `ReportFeature[]`
- Added "Meus relatos (anônimos)" checkbox to `FilterPanel` — visible only when user is null AND `localStorage['fala_gavea_anon_token']` is set

### Build result
`npm run build` passed: tsc + vite build succeeded, 273 modules transformed, 0 type errors.

### Status: SUCCESS
