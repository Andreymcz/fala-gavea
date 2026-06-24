# Progress -- Plan 000156

Append-only cross-iteration learnings. Each subagent reads this file at the start and appends findings at the end.

## Codebase Patterns

- Pages are in `frontend/src/features/` NOT `frontend/src/pages/` (no pages/ dir)
- Central API client: `frontend/src/lib/api.ts` (class with methods), imported via `@/lib/api`
- Types: `frontend/src/lib/types.ts`
- Hooks: `frontend/src/hooks/` (e.g., useReports.ts uses `api.createReport(body)`)
- Auth hook: `useAuth()` from `@/auth/AuthContext` → `{ token: string|null, user: User|null, ... }`
- React Query: `@tanstack/react-query` (useQuery, useMutation, useQueryClient)
- @/ alias maps to frontend/src/
- `frontend/src/api/` currently only has `nlFilter.ts` — new api files should go here
- Routing is in `frontend/src/App.tsx` (not main.tsx) using react-router-dom
- TableView dialog: `frontend/src/features/workspace/views/TableView.tsx`
- CestaView: `frontend/src/features/workspace/views/CestaView.tsx`
- Backend vote endpoints from plan-000153: POST /votes, DELETE /votes/{target_type}/{target_id}, GET /votes/{target_type}/{target_id}/summary
- VoteSummary: `{ upvotes: number; downvotes: number; user_vote: 1 | -1 | null }`

## Iteration Log
