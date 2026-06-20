# Research 000110 | feat/admin | 2026-06-20 20:33 UTC | Frontend view for feature 109 admin ops
tags: admin, frontend, feature-109, ui-coverage
spawned: plan-000112

## User Brief

Is there any frontend view for the operations in feature 109?

## Agent Interpretation

Feature 109 (plan-000109) added three backend admin operations:
1. **Bootstrap admin user** — auto-created on startup via env vars (`FALA_GAVEA_ADMIN_EMAIL`, `FALA_GAVEA_ADMIN_PASSWORD`)
2. **Seed topicos** — `POST /admin/seed/topicos` (CSV upload, admin-only)
3. **Wipe database** — `DELETE /admin/seed/wipe` (admin-only, with `include_report_types` flag)

The question asks whether any React frontend page or component exposes these operations to admin users.

## Files Reviewed

- `_output/plans/plan-000109-admin-seed-topicos-wipe.md` — feature scope
- `frontend/src/**/*.tsx` — all frontend components (grepped for admin/wipe/seed/topicos/bootstrap)

## Q&A Log

**Q1:** Is there any frontend view for these operations in feature 109?

**A1:** No — there is no frontend UI for any of the three feature-109 admin operations. Searching all `.tsx` files for `admin`, `wipe`, `seed`, `topicos`, and `bootstrap` yields only:

- Role-check guards (`user.role === 'admin'`) in Header, WorkspacePage, ViewToggleBar, MapView, TopicsView, ChatView, TableView — these control visibility of agent/admin features in the workspace, not admin management pages.
- `similarSeedId` in the workspace store — unrelated to the seed endpoints; it's for "find similar reports" in semantic search.

There is no `AdminPage.tsx`, no admin route in `App.tsx`, and no API calls to `/admin/seed/topicos` or `/admin/seed/wipe` anywhere in the frontend source.

## Recommendations Summary

1. **(HIGH)** If admin users need to trigger these operations from the browser, an Admin Panel page is missing. It should include: CSV upload form for seeding topicos, wipe controls with a confirmation dialog, and display of the bootstrap admin status. Add a route (e.g. `/admin`) in `App.tsx` guarded by `RequireAuth roles={["admin"]}`.

2. **(LOW)** If the intent is CLI/API-only admin ops (curl, Swagger UI), no frontend work is needed — document this in `product-design-as-coded.md` to clarify the gap is intentional.
