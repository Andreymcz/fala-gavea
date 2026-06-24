# Plan 000156 | feat/votes-ux | 2026-06-24 00:26 UTC | Vote UX: vote buttons on relato and forwarding cards | Review: light
plan_format_version: 1

source: roadmap-000151

## Brief

Add vote buttons (upvote/downvote with counts) to the relato detail view and to the public forwarding card in the frontend. Wire them to the new vote API endpoints from plan-000153.

## Context

Backend vote endpoints are available from plan-000153. The current frontend has:
- `WorkspacePage` with `TableView` (relato rows) and `CestaView`
- `/agent` page (`ForwardingsPage`) with forwarding cards
- Public forwarding reads via `GET /forwardings/public*`

Vote buttons appear in two places: on relato detail (inside the full-text dialog in TableView and CestaView) and on the forwarding public view (visible to any citizen on the citizen-facing forwarding list).

Self-voting: the backend returns 409; the frontend hides the button when the current user is the report/forwarding author (use `GET /auth/me` data already in the auth store).

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Vote button location | Relato full-text dialog + forwarding public card | Contextual; avoids cluttering the map/table views |
| Self-vote UI | Hide vote buttons when current_user.id == author_id | Cleaner than showing a disabled button with an explanation |
| Vote display for unauthenticated | Show counts, hide buttons | Transparency without friction |
| Optimistic update | Yes (local state flips immediately, rollback on API error) | Perceived responsiveness on mobile |

## Steps

### Step 1: API client functions for votes

Add to `frontend/src/api/votes.ts`:

```typescript
export async function castVote(targetType: 'report' | 'forwarding', targetId: string, value: 1 | -1, token: string): Promise<VoteSummary>
export async function retractVote(targetType: 'report' | 'forwarding', targetId: string, token: string): Promise<void>
```

Add `VoteSummary` type: `{ upvotes: number; downvotes: number; user_vote: 1 | -1 | null }`.

- **Files**: `frontend/src/api/votes.ts` (create)
- **Tests**: N/A
- [ ] Done

### Step 2: VoteButtons component

Create `frontend/src/components/VoteButtons.tsx`:

```tsx
interface Props {
  summary: VoteSummary | null
  onVote: (value: 1 | -1) => void
  onRetract: () => void
  disabled?: boolean  // true when user is author
  loading?: boolean
}
```

Renders two buttons: `▲ N` (upvote) and `▼ M` (downvote). Active state highlighted for `user_vote`. Calls `onVote(1)`, `onVote(-1)`, or `onRetract()` (clicking active vote retracts it). No buttons rendered if `disabled=true`. Fully controlled — parent manages state.

- **Files**: `frontend/src/components/VoteButtons.tsx` (create)
- **Tests**: N/A
- [ ] Done

### Step 3: Integrate into relato full-text dialog (TableView)

In the existing Radix Dialog full-text view in `TableView.tsx` (or the shared relato detail modal), add a `VoteButtons` row below the relato text. Use `react-query` mutation (`useMutation`) to call `castVote` / `retractVote`. Initialize from `report.votes` field (returned by the API in `VoteSummary` shape). Apply optimistic update via `queryClient.setQueryData`.

Hide vote buttons when `useAuth().user?.id === report.author_id` (authenticated authors cannot vote on own report; anonymous reports have `author_id = null` so the check passes and buttons are shown).

- **Files**: `frontend/src/features/workspace/views/TableView.tsx` (modify)
- **Verify**: Opening a relato dialog shows vote counts; clicking upvote increments the count and highlights the button; clicking again retracts
- **Tests**: N/A
- [ ] Done

### Step 4: Integrate into forwarding public card (citizen transparency view)

The citizen-facing forwarding list (consuming `GET /forwardings/public`) renders forwarding cards. Add `VoteButtons` to each card. Initialize from `forwarding.votes` field. Authenticated agents/admins see vote buttons; unauthenticated citizens see counts only (no buttons rendered when no JWT token).

- **Files**: `frontend/src/features/workspace/views/CestaView.tsx` or the shared forwarding card component (modify)
- **Verify**: Forwarding card shows vote counts; agent can upvote; citizen without account sees counts only
- **Tests**: N/A
- [ ] Done

## Pending Actions

- [ ] **implement** — Execute plan-000156 (votes-ux)
