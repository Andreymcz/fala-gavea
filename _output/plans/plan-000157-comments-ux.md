# Plan 000157 | feat/comments-ux | 2026-06-24 00:26 UTC | Comment UX: comment section on forwarding detail | Review: light
plan_format_version: 1

source: roadmap-000151

## Brief

Add a comment section to the forwarding detail view in the frontend. Wire to the new comment endpoints from plan-000154. Any authenticated user can add a comment; owner or agent/admin can delete it.

## Context

Backend comment endpoints are available from plan-000154. Comments are public (unauthenticated citizens can read), but only authenticated users can write. The forwarding detail is visible:
- For agents: in `ForwardingsPage` (`/agent`) via expandable rows or a detail modal
- For citizens: in the public forwarding view (from `GET /forwardings/public/{id}`)

## Steps

### Step 1: API client functions for comments

Add to `frontend/src/api/comments.ts`:

```typescript
export async function listComments(forwardingId: string): Promise<Comment[]>
export async function addComment(forwardingId: string, text: string, token: string): Promise<Comment>
export async function deleteComment(forwardingId: string, commentId: string, token: string): Promise<void>
```

Add `Comment` type: `{ id: string; forwarding_id: string; author_id: string; text: string; created_at: string }`.

- **Files**: `frontend/src/api/comments.ts` (create)
- **Tests**: N/A
- [x] Done

### Step 2: CommentSection component

Create `frontend/src/components/CommentSection.tsx`:

- Uses `react-query` `useQuery` to fetch comments via `listComments(forwardingId)` (public, no token needed)
- Shows a flat chronological list of comments with author_id (truncated to first 8 chars as display name if no name field) and `created_at` date
- Shows a text input + "Comentar" button for authenticated users (`useAuth().token !== null`)
- "Comentar" calls `addComment` via `useMutation`, invalidates the comments query on success
- Shows a trash icon on each comment for: comment author (same `user.id`) or agent/admin role; trash calls `deleteComment` via `useMutation`
- Text input validates 1–500 chars before enabling submit
- Shows pt-BR placeholder: "Adicione um comentário sobre este encaminhamento..."

- **Files**: `frontend/src/components/CommentSection.tsx` (create)
- **Tests**: N/A
- [x] Done

### Step 3: Integrate into agent ForwardingsPage

In `frontend/src/pages/ForwardingsPage.tsx`, add `<CommentSection forwardingId={forwarding.id} />` below the expandable row's report list (or inside the detail panel). This gives agents context on community reactions to their forwardings.

- **Files**: `frontend/src/features/forwardings/ForwardingRow.tsx` (modify)
- **Verify**: Expanding a forwarding row shows existing comments and an input; agent can add and delete comments
- **Tests**: N/A
- [x] Done

### Step 4: Integrate into public forwarding detail (citizen view)

In the citizen-facing forwarding detail view (if a modal/page exists consuming `GET /forwardings/public/{id}`), add `<CommentSection forwardingId={forwarding.id} />`. Unauthenticated citizens can read but not write.

If no citizen-facing forwarding detail page exists yet, create a minimal `ForwardingDetailPage` at `/forwardings/{id}` that fetches from `GET /forwardings/public/{id}` and renders the details + `<CommentSection>`. Link to it from the citizen relato detail (forwarding list for a relato).

- **Files**: `frontend/src/features/forwardings/PublicForwardingRow.tsx` (modify — added CommentSection inline in expanded row)
- **Verify**: Citizen expands a forwarding card and sees comments; authenticated citizen can add a comment
- **Tests**: N/A
- [x] Done

## Pending Actions

- [ ] **implement** — Execute plan-000157 (comments-ux)
