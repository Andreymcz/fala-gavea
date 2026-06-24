# DONE | 2026-06-24 18:36 UTC | Plan 000164 | feat/meus-relatos-votes-ux | 2026-06-24 18:01 UTC | Meus relatos nav + inline votes (table, map, sort) + vote API fix | Review: standard
plan_format_version: 1

source: reflection-000163

## Brief

Three UX gaps found during manual testing of roadmap-000151:

A. Citizens have no navigation entry point to "Meus relatos" — the filter exists in the left panel but is invisible unless the user already knows to look there.  
B. Votes are only accessible inside the relato full-text dialog — citizens cannot see or cast votes from the table row or map popup.  
C. Reports cannot be sorted by vote count (likes).

Root cause also found: `frontend/src/api/votes.ts` uses wrong endpoint URLs — `POST /votes` and `GET /votes/report/{id}/summary` — neither exists in the backend. Voting has been silently failing since roadmap-000151 shipped.

## Context

- Backend vote endpoints (from plan-000153): `POST /reports/{id}/votes`, `DELETE /reports/{id}/votes`, `POST /forwardings/{id}/votes`, `DELETE /forwardings/{id}/votes` — no GET summary endpoint exists.
- Frontend `VoteButtons.tsx` returns `null` when `disabled=true`; needs a `readOnly` mode to show counts without click handlers.
- `workspaceStore` has `setDraftFilter` + `applyFilters` actions that can be called from outside the panel.
- `ReportPopup` mounts lazily (only on marker click) so one fetch per open is acceptable.

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Batch vote summary endpoint | `GET /votes/reports/summary?ids=...` on new `votes_summary_router` | Avoids N+1 requests for table page (50 rows); no path conflicts with existing `/reports/{id}/votes` routes |
| GET single summary URL | `GET /reports/{id}/votes` (same path as POST/DELETE, different method) | Symmetric; no new path segment needed |
| VoteButtons readOnly mode | New `readOnly` prop on existing component | Avoids creating a second component for the same visual; table shows counts for all, buttons only for eligible voters |
| "Meus relatos" nav | URL param `?meus_relatos=1` + `useEffect` in WorkspacePage | No new route or page needed; reuses existing filter machinery |
| Sort by likes | Local client-side sort within current page using loaded vote summaries | Simple; avoids backend changes; works for pages of ≤50 rows |

## Steps

### Step 1: Backend — `get_optional_user` dependency

Add to `src/fala_gavea/presentation/api/dependencies.py`:

```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    user_repo: IUserRepository = Depends(get_user_repo),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt_service.decode_token(token)
        user_id: str = payload.get("sub", "")
        return user_repo.find_by_id(user_id)
    except Exception:
        return None
```

- **Files**: `src/fala_gavea/presentation/api/dependencies.py` (modify)
- **Tests**: N/A (thin wrapper around existing JWT logic)
- [x] Done

### Step 2: Backend — batch summary repo method

Add to `src/fala_gavea/domain/repositories/vote_repository.py`:

```python
@abstractmethod
def get_summaries_batch(
    self, target_type: str, target_ids: list[str], voter_id: str | None = None
) -> dict[str, VoteSummary]: ...
```

Implement in `src/fala_gavea/infrastructure/repositories/vote_repository.py`:

```python
def get_summaries_batch(
    self, target_type: str, target_ids: list[str], voter_id: str | None = None
) -> dict[str, VoteSummary]:
    if not target_ids:
        return {}
    # Count upvotes and downvotes per target in two queries
    up_rows = self._session.execute(
        select(VoteModel.target_id, func.count())
        .where(VoteModel.target_type == target_type, VoteModel.target_id.in_(target_ids), VoteModel.value == 1)
        .group_by(VoteModel.target_id)
    ).all()
    down_rows = self._session.execute(
        select(VoteModel.target_id, func.count())
        .where(VoteModel.target_type == target_type, VoteModel.target_id.in_(target_ids), VoteModel.value == -1)
        .group_by(VoteModel.target_id)
    ).all()
    upvotes: dict[str, int] = {r[0]: r[1] for r in up_rows}
    downvotes: dict[str, int] = {r[0]: r[1] for r in down_rows}
    user_votes: dict[str, int] = {}
    if voter_id:
        uv_rows = self._session.execute(
            select(VoteModel.target_id, VoteModel.value)
            .where(VoteModel.voter_id == voter_id, VoteModel.target_type == target_type, VoteModel.target_id.in_(target_ids))
        ).all()
        user_votes = {r[0]: r[1] for r in uv_rows}
    return {
        tid: VoteSummary(
            upvotes=upvotes.get(tid, 0),
            downvotes=downvotes.get(tid, 0),
            user_vote=user_votes.get(tid),
        )
        for tid in target_ids
    }
```

- **Files**: `src/fala_gavea/domain/repositories/vote_repository.py` (modify), `src/fala_gavea/infrastructure/repositories/vote_repository.py` (modify)
- **Tests**: add `tests/infrastructure/test_vote_repository_batch.py` with a test that inserts 3 report votes and asserts batch summary returns correct upvotes/downvotes counts per id
- [x] Done

### Step 3: Backend — add GET summary endpoints + batch router

In `src/fala_gavea/presentation/api/routers/votes.py`:

1. Add `GetVoteSummaryUseCase` dependency to the GET handlers.
2. Add `GET /{report_id}/votes` to `reports_votes_router` (optional auth, returns VoteSummarySchema):

```python
@reports_votes_router.get("/{report_id}/votes", response_model=VoteSummarySchema)
def get_report_vote_summary(
    report_id: str,
    current_user: User | None = Depends(get_optional_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> VoteSummarySchema:
    use_case = GetVoteSummaryUseCase(vote_repo)
    summary = use_case.execute("report", report_id, current_user.id if current_user else None)
    return _to_summary_schema(summary)
```

3. Add `GET /{forwarding_id}/votes` to `forwardings_votes_router` (same pattern).

4. Create a new `votes_summary_router = APIRouter()` in the same file with a batch endpoint:

```python
votes_summary_router = APIRouter()

@votes_summary_router.get("/reports/summary", response_model=dict[str, VoteSummarySchema])
def batch_report_vote_summaries(
    ids: str = Query(..., description="Comma-separated report IDs"),
    current_user: User | None = Depends(get_optional_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> dict[str, VoteSummarySchema]:
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        return {}
    use_case_cls = GetVoteSummaryUseCase  # not used; call repo directly for batch
    summaries = vote_repo.get_summaries_batch("report", id_list, current_user.id if current_user else None)
    return {tid: _to_summary_schema(s) for tid, s in summaries.items()}
```

5. In `src/fala_gavea/presentation/api/main.py`, add:
```python
from fala_gavea.presentation.api.routers.votes import votes_summary_router
app.include_router(votes_summary_router, prefix="/votes", tags=["votes"])
```

- **Files**: `src/fala_gavea/presentation/api/routers/votes.py` (modify), `src/fala_gavea/presentation/api/main.py` (modify)
- **Verify**: `curl /reports/{id}/votes` returns `{"upvotes":0,"downvotes":0,"user_vote":null}`; `curl /votes/reports/summary?ids=id1,id2` returns dict
- **Tests**: add basic route smoke test in existing `tests/api/` suite
- [x] Done

### Step 4: Frontend — fix `api/votes.ts` endpoint paths

Replace all three functions with correct URLs and add `getVoteSummaryBatch`:

```typescript
const BASE_URL = (import.meta.env.VITE_API_URL as string) || "";

function segment(targetType: "report" | "forwarding"): string {
  return targetType === "report" ? "reports" : "forwardings";
}

export async function getVoteSummary(
  targetType: "report" | "forwarding",
  targetId: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`);
  if (!res.ok) throw new Error("Failed to fetch vote summary");
  return res.json();
}

export async function castVote(
  targetType: "report" | "forwarding",
  targetId: string,
  value: 1 | -1,
  token: string,
): Promise<VoteSummary> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ value }),
  });
  if (!res.ok) throw new Error("Failed to cast vote");
  return res.json();
}

export async function retractVote(
  targetType: "report" | "forwarding",
  targetId: string,
  token: string,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/${segment(targetType)}/${targetId}/votes`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok && res.status !== 404) throw new Error("Failed to retract vote");
}

export async function getVoteSummaryBatch(
  reportIds: string[],
  token?: string | null,
): Promise<Record<string, VoteSummary>> {
  if (reportIds.length === 0) return {};
  const params = new URLSearchParams({ ids: reportIds.join(",") });
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}/votes/reports/summary?${params}`, { headers });
  if (!res.ok) throw new Error("Failed to fetch vote summaries");
  return res.json();
}
```

- **Files**: `frontend/src/api/votes.ts` (rewrite)
- **Tests**: N/A (unit test would mock fetch; integration covered by manual verify)
- [x] Done

### Step 5: Frontend — update `VoteButtons.tsx` to support `readOnly` mode

Add `readOnly?: boolean` prop. When `readOnly=true`, show counts as plain text spans with no click handlers (for unauthenticated users or report authors):

```tsx
interface Props {
  summary: VoteSummary | null;
  onVote: (value: 1 | -1) => void;
  onRetract: () => void;
  disabled?: boolean;   // hides the component entirely (unchanged)
  readOnly?: boolean;   // shows counts but no click handlers
  loading?: boolean;
}

export function VoteButtons({ summary, onVote, onRetract, disabled, readOnly, loading }: Props) {
  if (disabled) return null;

  const userVote = summary?.user_vote ?? null;

  function handleClick(value: 1 | -1) {
    if (readOnly || loading) return;
    if (userVote === value) onRetract();
    else onVote(value);
  }

  const upClass = userVote === 1 ? "bg-green-100 text-green-700 font-semibold" : "bg-gray-100 text-gray-600";
  const downClass = userVote === -1 ? "bg-red-100 text-red-700 font-semibold" : "bg-gray-100 text-gray-600";

  return (
    <div className="flex items-center gap-1 text-sm">
      <button
        type="button"
        onClick={() => handleClick(1)}
        disabled={readOnly || loading}
        className={`flex items-center gap-0.5 rounded px-1.5 py-0.5 transition-colors text-xs ${upClass} ${!readOnly ? "hover:bg-green-50" : "cursor-default"}`}
        aria-label="Votar a favor"
      >
        ▲ {summary?.upvotes ?? 0}
      </button>
      <button
        type="button"
        onClick={() => handleClick(-1)}
        disabled={readOnly || loading}
        className={`flex items-center gap-0.5 rounded px-1.5 py-0.5 transition-colors text-xs ${downClass} ${!readOnly ? "hover:bg-red-50" : "cursor-default"}`}
        aria-label="Votar contra"
      >
        ▼ {summary?.downvotes ?? 0}
      </button>
    </div>
  );
}
```

- **Files**: `frontend/src/components/VoteButtons.tsx` (modify)
- **Tests**: N/A
- [x] Done

### Step 6: Frontend — "Meus relatos" header link + WorkspacePage init

**Header.tsx**: add "Meus relatos" link for any authenticated user (after the existing nav links):

```tsx
{user && (
  <Link to="/?meus_relatos=1" className="text-sm text-gray-600 hover:text-gray-900">
    Meus relatos
  </Link>
)}
```

Place it after the "Novo relato" link and before "Encaminhamentos".

**WorkspacePage.tsx**: add a `useEffect` that reads the `?meus_relatos=1` query param on mount and pre-applies the author filter:

```tsx
import { useLocation, useNavigate } from 'react-router-dom'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { useAuth } from '@/auth/AuthContext'

// Inside WorkspacePage, after existing hooks:
const location = useLocation()
const navigate = useNavigate()
const setDraftFilter = useWorkspaceStore((s) => s.setDraftFilter)
const applyFilters = useWorkspaceStore((s) => s.applyFilters)

useEffect(() => {
  const params = new URLSearchParams(location.search)
  if (params.get('meus_relatos') === '1' && user) {
    setDraftFilter({ author_id: user.id })
    applyFilters()
    // Clean the URL param without re-rendering
    navigate('/', { replace: true })
  }
}, [])  // intentional: run once on mount only
```

- **Files**: `frontend/src/components/layout/Header.tsx` (modify), `frontend/src/features/workspace/WorkspacePage.tsx` (modify)
- **Verify**: clicking "Meus relatos" in header navigates to `/` with filter pre-applied; only user's own relatos are shown in table; URL param disappears from address bar after apply
- **Tests**: N/A
- [x] Done

### Step 7: Frontend — inline votes in TableView rows (display + vote + sort by votes)

**7a — Vote summaries state**: in `TableView`, replace the single `voteSummary` state with a map covering all page items:

```tsx
const [voteSummaries, setVoteSummaries] = useState<Map<string, VoteSummary>>(new Map())

// Fetch batch on page load / whenever sorted ids change
const sortedIds = sorted.map((f) => f.properties.id)
useEffect(() => {
  if (sortedIds.length === 0) return
  getVoteSummaryBatch(sortedIds, token ?? null)
    .then((batch) => setVoteSummaries(new Map(Object.entries(batch))))
    .catch(() => {})
}, [sortedIds.join(','), token])
```

Keep the single-dialog `voteSummary` state and its effect (for dialog detail view) but initialize it from the map if already loaded.

**7b — Sort by votes**: add `'upvotes'` to `SortKey` type and handle it in the `sorted` computation:

```tsx
case 'upvotes': {
  const sa = voteSummaries.get(pa.id)?.upvotes ?? 0
  const sb = voteSummaries.get(pb.id)?.upvotes ?? 0
  return mult * (sa - sb)
}
```

Add a "Votos" column header with sort button (same pattern as other columns).

**7c — Inline VoteButtons per row**: in each `TableRow`, add a cell after the existing cells:

```tsx
<TableCell className="text-center">
  <VoteButtons
    summary={voteSummaries.get(p.id) ?? null}
    onVote={async (v) => {
      if (!token) return
      const updated = await castVote('report', p.id, v, token)
      setVoteSummaries((prev) => new Map(prev).set(p.id, updated))
    }}
    onRetract={async () => {
      if (!token) return
      await retractVote('report', p.id, token)
      const updated = await getVoteSummary('report', p.id)
      setVoteSummaries((prev) => new Map(prev).set(p.id, updated))
    }}
    disabled={false}
    readOnly={!token || (user?.id != null && user.id === p.author_id)}
    loading={false}
  />
</TableCell>
```

When the user casts a vote inline and the dialog is open for the same report, also update `voteSummary` to keep dialog in sync.

- **Files**: `frontend/src/features/workspace/views/TableView.tsx` (modify)
- **Verify**: table shows ▲ N ▼ M on each row; authenticated non-author can click to vote; author's rows show counts only (readOnly); sort by Votos reorders current page
- **Tests**: N/A
- [x] Done

### Step 8: Frontend — VoteButtons in ReportPopup (map)

`ReportPopup` currently has no auth context. Add vote state and actions:

```tsx
import { useAuth } from '@/auth/AuthContext'
import { VoteButtons } from '@/components/VoteButtons'
import { getVoteSummary, castVote, retractVote } from '@/api/votes'
import type { VoteSummary } from '@/lib/types'
import { useState, useEffect } from 'react'

// Inside ReportPopup:
const { user, token } = useAuth()
const [voteSummary, setVoteSummary] = useState<VoteSummary | null>(null)

useEffect(() => {
  getVoteSummary('report', p.id).then(setVoteSummary).catch(() => {})
}, [p.id])

async function handleVote(value: 1 | -1) {
  if (!token) return
  const updated = await castVote('report', p.id, value, token)
  setVoteSummary(updated)
}

async function handleRetract() {
  if (!token) return
  await retractVote('report', p.id, token)
  const updated = await getVoteSummary('report', p.id)
  setVoteSummary(updated)
}
```

Render at the bottom of the popup JSX (after the `{dateStr}` line and before the agent checkbox):

```tsx
<VoteButtons
  summary={voteSummary}
  onVote={handleVote}
  onRetract={handleRetract}
  disabled={false}
  readOnly={!token || (user?.id != null && user.id === p.author_id)}
/>
```

- **Files**: `frontend/src/features/map/ReportPopup.tsx` (modify)
- **Verify**: opening a map marker popup shows vote counts; authenticated non-author can vote inline; vote count updates immediately
- **Tests**: N/A
- [x] Done

## Docs

No documentation changes required — this plan fixes a bug and adds UX improvements to existing features described in roadmap-000151.

## Pending Actions

- [ ] **test-implementation** — after implementation, test: (1) "Meus relatos" header link applies filter; (2) vote buttons appear in table rows for all users; (3) vote buttons appear in map popup; (4) sort by Votos reorders current page; (5) voting via table/map persists correctly

## Implementation Summary

**Completed:** 2026-06-24 18:36 UTC | 8/8 steps | 0 partial/failed | commit 9175d90

### What was implemented

**Backend (Steps 1-3):**
- `get_optional_user` dependency in `dependencies.py` — uses `oauth2_scheme_optional` (auto_error=False), catches only `InvalidCredentialsError`
- `get_summaries_batch` on `IVoteRepository` (abstract) + `SQLAlchemyVoteRepository` (3 queries: upvotes, downvotes, user votes)
- `GET /reports/{id}/votes` and `GET /forwardings/{id}/votes` (optional auth, returns VoteSummarySchema)
- `GET /votes/reports/summary?ids=...` batch endpoint (max 200 IDs, registered as `votes_summary_router`)

**Frontend (Steps 4-8):**
- `api/votes.ts` — fixed all 3 endpoint URLs; added `getVoteSummaryBatch`
- `VoteButtons.tsx` — added `readOnly` prop; shows counts without click handlers when true
- `Header.tsx` — "Meus relatos" link (visible to authenticated users) navigates to `/?meus_relatos=1`
- `WorkspacePage.tsx` — `useEffect` on mount applies `author_id` filter and clears URL param
- `TableView.tsx` — batch vote fetch on page load; `SortKey` extended with `'upvotes'`; inline VoteButtons per row; `colSpan` corrected; dialog VoteButtons aligned to `readOnly`
- `ReportPopup.tsx` — vote state + handlers; `VoteButtons` rendered after date line

### Review findings resolved
- Narrowed `except Exception` → `except InvalidCredentialsError` in `get_optional_user`
- Added 200-ID cap on batch endpoint
- Aligned dialog VoteButtons to `readOnly` (was `disabled`, which hides the component)
