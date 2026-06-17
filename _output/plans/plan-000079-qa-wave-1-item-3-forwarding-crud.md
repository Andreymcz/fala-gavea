# QA Log 000080 | plan-000079 | 2026-06-17 22:33 UTC | wave-1-item-3-forwarding-crud

source: plan-000079

## Brief

roadmap 1 item 3

## Q&A Log

**Q: What does "roadmap 1 item 3" mean in context?**

A: Item 3 of Wave 1 in roadmap-000071. Scope: Forwarding CRUD -- 5 endpoints (POST create,
GET list, GET detail, PATCH update, PATCH status) all requiring agent or admin role. The
Forwarding entity, SQLAlchemy model (ForwardingModel), and join table model (ForwardingReportModel)
were created in plan-000073. This plan adds the repository layer, use cases, schemas, and router.

**Q: Why does CreateForwarding update report statuses in the same use case rather than a
separate status-update use case?**

A: The roadmap spec explicitly states: "Ao criar um Forwarding, todos os Reports incluidos
transitam para status `encaminhado`". This is a business invariant -- creating the forwarding
and transitioning the reports is a single atomic operation. Separating it into two use cases
would expose an inconsistent intermediate state (forwarding created, reports still pending).

**Q: Why add `require_any_role` to dependencies.py instead of checking role in the router?**

A: Constitution T2 mandates "nenhum router acessa JWT diretamente; use dependencies.py
(get_current_user, require_role)". The spirit of this principle is that role enforcement lives
in the dependency layer, not in router function bodies. `require_any_role(*roles)` is a clean
extension of the existing `require_role(role)` pattern.

**Q: What's the N+1 query issue in GetForwarding and why is it deferred?**

A: `get_report_ids()` returns a list of IDs, then the use case calls `report_repo.find_by_id()`
for each one -- N round trips to SQLite for N linked reports. For the PoC scale (a forwarding
typically contains 2-10 reports), this is imperceptible. A future join query could return
(Forwarding, list[Report]) in one SELECT. Deferred because SQLite local access is fast
and the PoC doesn't require optimization.

**Q: Why does `ForwardingUpdate` allow partial updates (both fields optional)?**

A: PATCH semantics per RFC 5789 -- only provided fields should be updated. An agent may want
to correct only the institution name without re-typing the proposed_solution. The use case
handles "if field is not None: update" logic, so a PATCH with an empty body is a no-op (valid,
returns the unchanged forwarding).

**Q: Does this plan depend on plan-000075 being implemented first?**

A: Only for the `admin_headers` fixture in conftest.py (added by plan-000075). The forwardings
tests use `agent_headers` (already in conftest) for all forwarding operations; admin is not
needed for forwarding endpoints. However, to test forwarding creation, a ReportType must exist
(needed to create a Report). Tests create a ReportType via the fixture from conftest
(`sample_report_type`) which uses the repository directly -- no dependency on plan-000075's
HTTP endpoints.
