# QA Log — implement 000169 — GET /forwardings/mine — encaminhamentos do cidadão

**Brief:** GET /forwardings/mine — encaminhamentos do cidadão logado. plan 000169
**Date:** 2026-06-24 20:32 UTC
**Skill:** implement
**Plan:** 000169

## Q&A

**Q:** How is the `GET /forwardings/mine` endpoint protected?
**A:** Uses `get_current_user` dependency (JWT Bearer, any role: citizen/agent/admin). Returns 401 for unauthenticated requests. `current_user.id` is extracted server-side — never from URL or request body.

**Q:** How does the repository query work?
**A:** `find_by_author_id` uses a DISTINCT JOIN: `ForwardingModel → ForwardingReportModel → ReportModel` filtering on `ReportModel.author_id == author_id`. DISTINCT prevents duplicates when a citizen's report appears in multiple forwardings.

**Q:** Why is the route registered before `GET /{id}`?
**A:** FastAPI matches routes in registration order. Without pre-registration, the string "mine" would be interpreted as a forwarding UUID path parameter, causing a 404/500 instead of routing to the correct handler. Same pattern as `/public` and `/public/{id}`.

**Q:** Why `PublicForwardingResponse` (no `agent_id`)?
**A:** Consistent with the citizen-transparency surface (D-011 pattern). Citizens don't need to know the internal agent identity; `PublicForwardingResponse` omits `agent_id` per design.

**Q:** How does the frontend prevent unnecessary 401 calls for unauthenticated users?
**A:** `useMyForwardings(enabled=!!user)` passes `enabled: false` to React Query when there's no logged-in user, preventing the query from firing. Without this guard, the query would trigger on page load for all visitors, dispatching `auth:unauthorized` events even for unauthenticated users browsing `/encaminhamentos`.

## Test Results

- `uv run pytest tests/test_forwardings.py -v` → 16 passed, 0 failed (13 pre-existing + 3 new: test_mine_returns_forwarding_with_own_reports, test_mine_excludes_forwardings_of_other_citizens, test_mine_requires_auth)
- `uv run pyright src/` → no new errors introduced (pre-existing 89 errors unchanged)
