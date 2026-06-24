# Research 000150 | feature-design | 2026-06-24 00:06 UTC | Citizen feedback (votes + comments) and anonymization

source: reflection-000149
tags: feedback, anonymization, security, ux, data-model

**User brief:** investigate the citizen feedback mechanism (votes + comments) AND the blueprint gaps (anonymization) before planning. notifications not needed, gps is working on web, photo upload not needed

**Agent interpretation:** Two new features requested by the user after reflecting on the design blueprint (personas Ludmila + Maria Alice). Feature 1: citizens can upvote/downvote relatos and encaminhamentos, and add comments to encaminhamentos. Feature 2: anonymous/pseudonymous reporting to address Ludmila's trust barrier ("se puder fazer isso em sigilo talvez valha a pena"). GPS and photo upload confirmed as already working or explicitly out of scope.

**Files:**
- `product-design/project/product-design-as-coded.md` — current entity hierarchy and permission model
- `src/fala_gavea/domain/entities/` — pure Python dataclasses (User, Report, Forwarding, etc.)
- `src/fala_gavea/domain/repositories/` — port ABCs
- `src/fala_gavea/infrastructure/database/models.py` — SQLAlchemy models
- `src/fala_gavea/presentation/api/dependencies.py` — auth guards
- `src/fala_gavea/presentation/schemas/` — Pydantic request/response schemas
- `frontend/src/` — React SPA

---

## Q&A Log

**Q1.** How should fala-gavea model citizen votes (upvote/downvote) on relatos and encaminhamentos, and comments on encaminhamentos? And how should anonymous reporting be designed to satisfy Ludmila's trust requirement without breaking the "Meus relatos" tracking feature?

**A1.** See recommendations below (synthesized from a multi-perspective expert review).

---

## Analysis

### Feature 1 — Votes and Comments

**Vote entity vs. counter field.** A counter field on Report/Forwarding is irreversible, unauditable, and vulnerable to corruption. A separate `Vote` entity is strictly better: DB-guaranteed deduplication via a composite unique constraint, auditability, and retroactive abuse revocation. The query cost (COUNT GROUP BY) is negligible at SQLite PoC scale.

**Self-voting.** Block at the use-case layer: `CastVoteUseCase` compares `voter_id` against the target's `author_id` / `agent_id` and raises a domain exception. The frontend can hide the button but server-side enforcement is the real gate.

**Vote visibility.** In a small community (Gávea/Rocinha), exposing individual voter identities can enable retaliation and break trust. API responses expose only aggregated counts + the requesting user's own vote: `{upvotes: N, downvotes: M, user_vote: +1|-1|null}`.

**Comments.** Flat (no threading) is the right PoC scope. A comment attaches to a forwarding and carries the author. Moderation is delete-only via agent/admin. Defer full moderation workflow to future.

**Abuse.** The primary vector is vote-stuffing via account farming (low barrier in a civic app with email-only registration). A per-user rate limit on vote creation (e.g., 20 ops/min via slowapi, same pattern as `/nl/filter`) is a low-cost deterrent.

**Integration with agent prioritization.** Vote counts are visible data — agents can sort the forwarding list by net votes (`upvotes - downvotes`) as a community-signal filter. No changes to the semantic search ranker are needed for the PoC; ChromaDB ranking stays query-similarity based.

---

### Feature 2 — Anonymization

**The core tension.** The most privacy-preserving design (no server-side linkage) is the worst UX for a mobile user who needs to track their own report across sessions. The recommended resolution is a client-stored anonymous claim token (UUID) with a hashed version stored server-side — not on the Report row itself, but in a separate `AnonymousReportToken` table.

**Data model.** `Report.author_id` becomes nullable. A new `AnonymousReportToken` table holds `(id, report_id FK, token_hash, created_at)`. The UUID token is returned once in the POST /reports response body and never again. The client stores it in localStorage.

**Why a separate table (not a column on Report)?** Keeps the `Report` entity clean (no nullable proliferation), and makes future token expiry/purge independent of the Report lifecycle. One token per anonymous report; many anonymous reports can coexist.

**"Meus relatos" for anonymous users.** Two query paths in `ReportRepository`: authenticated → `WHERE author_id = current_user.id`; anonymous token holder → `WHERE id IN (SELECT report_id FROM anonymous_report_tokens WHERE token_hash = sha256(token))`. The token is passed as a query parameter (not in the Authorization header). The frontend stores the token and sends it when fetching "my anonymous reports".

**Re-identification mitigation.** In a geographically tight community, `lat/lon + timestamp + report_type` is nearly identifying. For anonymous reports, public API responses round lat/lon to ~3 decimal places (~110 m) and suppress the exact `created_at` (show date only). Full precision is retained in DB for agent analysis.

**Pseudonym user account (rejected).** Creates a DB identity record (a GDPR-registrable processing activity), adds account management complexity, and doesn't solve the "Meus relatos" problem any better than the token approach. Rejected.

**"Reclaim ownership" (deferred).** Linking an anonymous token to a logged-in user retroactively is complex and has a theft vector (anyone with the token can claim the report). Defer entirely for the PoC.

**UX copy.** At submission time, plain pt-BR: *"Ao enviar sem identificação, você receberá um código para acompanhar seu relato. Guarde esse código — sem ele não será possível acompanhar o andamento."* This is critical to prevent the "I reported and never found out what happened" breakdown (Frustration F-1 of persona R-P-001 Ludmila).

---

## Recommendations Summary

### HIGH

**R1 — Use a separate `Vote` entity (not counter field).**
`Vote(id, voter_id FK users, target_type ENUM('report','forwarding'), target_id, value ENUM(+1,-1), created_at)` with composite UNIQUE on `(voter_id, target_type, target_id)`. DB-guaranteed deduplication, auditable, abuse-reversible.

**R2 — Block self-voting at the use-case layer.**
`CastVoteUseCase` raises a domain exception when `voter_id == target.author_id` (or forwarding's `agent_id`). Frontend hides the button as a courtesy; server enforces.

**R3 — Use nullable `author_id` + separate `AnonymousReportToken` table.**
`Report.author_id: str | None`. New table `anonymous_report_tokens(id, report_id FK, token_hash TEXT, created_at)`. UUID token returned once at POST /reports; hashed server-side. Client stores in localStorage. Keeps Report entity clean; token lifecycle manageable independently.

**R4 — Coarsen geolocation for anonymous reports in public API responses.**
When `author_id IS NULL`, round lat/lon to 3 decimal places (~110 m) and return date-only for `created_at` in public-facing schemas. Full precision retained in DB for agent views.

### MEDIUM

**R5 — Expose aggregated vote counts + user's own vote only; never expose voter identity list.**
Response schema: `{upvotes: int, downvotes: int, user_vote: int | null}`. No endpoint exposes who voted for what.

**R6 — Keep comments flat, delete-only moderation (agent/admin).**
`Comment(id, forwarding_id FK, author_id FK, text 1–500 chars, created_at)`. No threading. DELETE endpoint gated to `require_any_role("agent", "admin")`. Citizens can delete their own comments via `require_role("citizen") + owner check`.

**R7 — "Meus relatos" supports both authenticated and token-based paths.**
`ReportRepository.find_page` gains an `anonymous_token_hash: str | None` parameter. The use case routes by auth type; the router accepts an optional `?anonymous_token=` query param for unauthenticated callers.

**R8 — Show clear anonymity consequences at submission time (pt-BR copy).**
*"Ao enviar sem identificação, você receberá um código para acompanhar seu relato. Guarde esse código — sem ele não será possível acompanhar o andamento."* Displayed once, prominently, before the user toggles to anonymous mode.

### LOW

**R9 — Rate-limit vote creation per authenticated user (20 ops/min via slowapi).**
Same pattern as POST /nl/filter. Deters scripted account farming without complex infrastructure.

**R10 — Defer "reclaim ownership" of anonymous reports.**
Retroactive linking of anonymous token to a logged-in account has a theft vector. Out of scope for the PoC.

**R11 — Defer comment moderation workflow (flag, review, hide).**
Delete-only via agent/admin is sufficient for the PoC. Document the absence of moderation in design intent.

---

## New entities and schema changes (summary for planning)

**New DB tables:**
- `votes(id, voter_id FK users, target_type TEXT CHECK('report','forwarding'), target_id TEXT, value INT CHECK(1,-1), created_at)` — UNIQUE(voter_id, target_type, target_id)
- `comments(id, forwarding_id FK forwardings, author_id FK users, text TEXT, created_at)` — FK CASCADE DELETE on forwardings.id
- `anonymous_report_tokens(id, report_id FK reports, token_hash TEXT NOT NULL UNIQUE, created_at)` — FK CASCADE DELETE on reports.id

**Modified DB tables:**
- `reports.author_id` — change from NOT NULL to nullable (Alembic migration required)

**New API endpoints:**
- `POST /reports/{id}/votes` (any auth user) — cast or change vote
- `DELETE /reports/{id}/votes` (any auth user) — retract vote
- `POST /forwardings/{id}/votes` (any auth user)
- `DELETE /forwardings/{id}/votes` (any auth user)
- `GET /forwardings/{id}/comments` (public)
- `POST /forwardings/{id}/comments` (any auth user)
- `DELETE /forwardings/{id}/comments/{comment_id}` (comment owner or agent+admin)
- `GET /reports?anonymous_token=` — retrieve anonymous user's own reports

**Modified API endpoints:**
- `POST /reports` — response body adds `anonymous_token: str | null` when submitted anonymously; request body adds `anonymous: bool = false`
- `GET /reports/geojson`, `GET /forwardings/public*` — response schemas add `votes: VoteSummary` field
