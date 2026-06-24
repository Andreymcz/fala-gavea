# QA Log | Plan 000164 | 2026-06-24 18:07 UTC | Meus relatos nav + inline votes + sort by votes

**Brief**: Planning session that started as a reflection on roadmap-000151, discovered two UX gaps (no citizen nav entry for "Meus relatos"; votes only accessible in dialog) plus a root-cause bug (frontend `api/votes.ts` uses wrong endpoint URLs), and produced plan-000164 to fix all three plus add inline votes on table rows and map popups with sort-by-likes capability.

---

## Q1
User invoked `/reflect what was deone in roadmap 151. and how to test it in front end`

## A1
Pre-skill ran (briefs logged, references loaded). Reflection ID 000163 reserved. Skipped AskUserQuestion for scope since the user already specified roadmap-000151. Read `roadmap-000151`, `plan-000156` (votes-ux), `plan-000157` (comments-ux), `plan-000158` (anon-ux) and presented a full summary covering: 3 waves (DB migrations → backend votes/comments/anon → frontend VoteButtons/CommentSection/anon toggle), plus a "How to test" table covering votes on relato dialog, votes on forwarding card, comment section for agents and citizens, anonymous submission toggle, and anonymous "Meus relatos" filter.

---

## Q2
User: "abri o site como cidadao e não vejo a página Meus relatos, que deveria listar meus relatos e os respectivos encaminhamentos. também não vejo possibilidade de dar likes para relatos"

## A2
Reflection captured as Step C verbatim. Wrote `reflection-000163-roadmap-151-frontend-gaps-votes-meus-relatos.md`.

Investigation: read `App.tsx`, `Header.tsx`, `FilterPanel.tsx`, `WorkspacePage.tsx`, `TableView.tsx`, `VoteButtons.tsx`, `api/votes.ts`, `votes.py` (backend).

**Findings:**
1. "Meus relatos" is a checkbox in the left FilterPanel — no header nav link for citizens.
2. VoteButtons are inside the relato full-text dialog; invisible until user clicks a row.
3. Critical bug found: `api/votes.ts` `getVoteSummary` calls `GET /votes/report/{id}/summary` and `castVote` calls `POST /votes` — neither endpoint exists in the backend (real endpoints are `POST /reports/{id}/votes`, `DELETE /reports/{id}/votes`, no GET summary at all). Voting silently fails for all users.

Proposed two correction paths: (A) header nav link to workspace with pre-applied filter; (B) votes visible inline on table rows and map popups.

---

## Q3
User invoked `/plan A e B, meus relatos leva ao workspace com filtro pre-aplicado. Votos visiveis na linha da tabela e passiveis de alteração via tabela. tambem pode ser possivel dar voto via mapa`

## A3
Auto-detection: 2 layers (backend fix + frontend UX); 3 UI surfaces (header, table, map). Resolved as single plan (all changes coherent, ≤12 steps).

Plan 000164 reserved. Read additionally: `vote_repository.py` (domain + infra), `dependencies.py`, `ReportPopup.tsx`, `workspaceStore.ts`.

---

## Q4 (mid-planning)
User: "os relatos tambem podem ser ordenados pelo numero de likes"

## A4
Added Step 7b to plan: extend `SortKey` type with `'upvotes'`, sort locally within current page using the loaded `voteSummaries` map.

---

## Plan 000164 written with 8 steps:

1. **Backend** — `get_optional_user` dependency (optional JWT auth)
2. **Backend** — `get_summaries_batch` on `IVoteRepository` + `SQLAlchemyVoteRepository` (2 GROUP BY queries)
3. **Backend** — `GET /{report_id}/votes` + `GET /{forwarding_id}/votes` (single summary, optional auth); `votes_summary_router` with `GET /votes/reports/summary?ids=...` (batch); mount at `/votes` in `main.py`
4. **Frontend** — fix `api/votes.ts`: correct URLs for `castVote`, `retractVote`, `getVoteSummary`; add `getVoteSummaryBatch`
5. **Frontend** — `VoteButtons.tsx`: add `readOnly` prop (shows counts, no click handlers)
6. **Frontend** — `Header.tsx` "Meus relatos" link for authenticated users → `/?meus_relatos=1`; `WorkspacePage.tsx` `useEffect` reads param, sets `author_id` filter, applies, cleans URL
7. **Frontend** — `TableView.tsx`: batch-fetch vote summaries per page; Votos column with inline `VoteButtons`; sort by `upvotes`
8. **Frontend** — `ReportPopup.tsx`: vote state + fetch on mount + `VoteButtons` at bottom of popup
