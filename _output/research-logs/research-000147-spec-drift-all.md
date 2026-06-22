# Research 000147 | spec-drift all | 2026-06-22 23:32 | spec-drift all

**User brief:** `/explain spec-drift` (scope: all -- conceptual-design + metacommunication)

**Agent interpretation:** Compare the registered as-intended spec (`product-design/project/product-design-as-intended.md`) against the as-coded spec (`product-design/project/product-design-as-coded.md`) and surface every divergence: features in code but absent from intent, intent items implemented but not marked, and stale sections in either file. Note: the internal sub-skill body (`.claude/skills/_internal/explain/spec-drift/SKILL.md`) referenced by `/explain` is not present in this harness install, so this is a best-effort drift analysis performed inline rather than via the dispatched sub-skill.

**Files:**

- As-intended: `product-design/project/product-design-as-intended.md`
- As-coded: `product-design/project/product-design-as-coded.md`
- Registry: `product-design/conventions.md` (As-Intended / As-Coded Registry)

---

## Summary

The two specs have **drifted substantially**. The dominant pattern is **as-coded lagging reality**: the entire roadmap-000146 work (cesta de relatos + citizen-transparency, committed across `95b5085 → eb4c98a`) is captured in design *intent* (Decisions D-010–D-013) and exists in code, but was **never written back to as-coded**. Secondary drift: as-intended carries several stale "nothing implemented yet / greenfield" sections (§16, §17) that are now wholly false, and 7 Decision entries (D-007–D-013) that are implemented but carry no `STATUS: implemented` marker. There are also implemented features (SavedFilter, TF-IDF keywords, NL filter, query endpoint, admin seed endpoints) that have no home in as-intended.

Drift count: **4 high**, **5 medium**, **3 low**. Aligned areas: core entities, core permission model, validation constants, JM-TB-001/002.

---

## High-severity drift

### H1. roadmap-000146 (cesta de relatos + citizen transparency) absent from as-coded

Intent records four decisions from research-000145 (2026-06-22):

- **D-010** -- "Relato aberto" = `ReportStatus.pendente` only (duplicate-detection semantics for the basket).
- **D-011** -- Public forwarding reads: new `GET /forwardings/public`, `GET /forwardings/public/{id}`, `GET /reports/{id}/forwardings` (schema without `agent_id`); POST/PATCH stay agent+admin.
- **D-012** -- Citizen relatos list = all reports + "Meus relatos" toggle; adds `author_id` to `ReportFilters`/queries + index on `reports.author_id`.
- **D-013** -- "Cesta de relatos" elevates `selectedIds`: count badge in Header + `cesta` view (map/table pair) with review + open-similars + inline creation; removes the floating SelectionBar.

Git log confirms implementation (`95b5085` Wave 0 backend, `e9cd693` Wave 1 basket, `f422022` Wave 2 citizen UX, `ca5bdb5` complete, `eb4c98a` telemetry). **as-coded contains none of this**: §1 endpoint list has no `/forwardings/public*` or `/reports/{id}/forwardings`; §4 permission model has no public-forwarding row; §8 has no `cesta` view and still describes the floating SelectionBar as present (plan-000137 entry); §2 `ReportFilters` description has no `author_id`. The as-coded Changelog stops well before roadmap-000146.

**Impact:** The as-coded mirror is the artifact post-skill is supposed to keep current; it is now the single most out-of-date file. Anyone reading as-coded would conclude the citizen-transparency journey does not exist.

### H2. as-intended §16 "Conceptual Design Delta" is entirely false

§16 still reads: New = "todas as entidades definidas no design intent, **nenhuma implementada ainda**"; Changed = "_N/A -- projeto greenfield, **nenhum codigo implementado ainda**._" Every entity, the permission model, all UX patterns, and JM-TB-001/002/003 are fully implemented (confirmed in as-coded §2–§8 and Journey Maps). This section was authored at greenfield and never maintained.

### H3. as-intended §17 "Metacommunication Delta" is false

§17 lists all five per-feature intentions under "New Intentions (**not yet implemented**)". Four of the five are implemented (form+geolocation, public map, multiple selection, semantic search), and the fifth (Chat NL) already carries a `STATUS: implemented | plan-000100` marker in §14/§17. The "not yet implemented" framing is stale.

### H4. Seven implemented Decisions lack `STATUS: implemented` markers

D-007 (SPA), D-008 (workspace grid), D-009 (staged filter draft+Apply), D-010, D-011, D-012, D-013 are all reflected in code/as-coded but carry **no STATUS marker** (D-001–D-006 are marked `proposed`; only §14/§17 Chat NL is marked `implemented`). These are the prime candidates for a `STATUS: implemented` promotion pass. Without markers, the lifecycle tooling cannot tell decided-and-shipped from decided-and-pending.

---

## Medium-severity drift

### M1. BERTopic replaced by TF-IDF keywords -- intent never updated

as-intended §8 ("topicos/clusters semanticos inferidos (**BERTopic**)") and JM-TB-003 step 5 ("topicos inferidos (BERTopic)") still describe BERTopic. as-coded §3 records that BERTopic went dormant (plan-000124), `GET /reports/topics` was **removed**, and a TF-IDF + K-means `GET /reports/keywords` endpoint replaced it, with the view renamed "Palavras-chave". Intent describes a capability the code deliberately dropped.

### M2. `SavedFilter` entity implemented, absent from intent

as-coded §2 lists a sixth entity `SavedFilter` (plan-000139: `saved_filters` table + 5 owner-scoped CRUD endpoints, BOLA-guarded). as-intended §2 Entity Hierarchy lists only five entities and has no Decision entry covering saved filters. Implemented capability with no design-intent anchor.

### M3. NL filter + unified query + admin seed endpoints absent from intent permission model

as-coded §1/§4 document `POST /reports/query`, `GET /reports/keywords`, `POST /nl/filter` (rate-limited), and `POST /admin/seed/relatos`, `POST /admin/seed/topicos`, `DELETE /admin/seed/wipe`. as-intended §4 Permission Model and §6 Import/Export do not mention any of these (§6 even says "importacao de dados externos e future work", contradicted by the CSV seed-upload endpoints). Intent's permission table is a strict subset of what shipped.

### M4. as-coded Journey Maps table internally inconsistent re: topics

The as-coded Journey Maps delta still labels JM-TB-003 step as "TopicsView (**BERTopic**)" even though as-coded §3/§8 in the same file say BERTopic is dormant and the view is now TF-IDF "Palavras-chave". This is drift *within* as-coded -- the Journey Maps section was not updated when plan-000124 swapped the implementation.

### M5. as-coded Metacommunication section is a near-stub

as-coded Metacommunication §1 (Global Summary), §2 (EMT), §3 (Solution Representations) all say "_Not yet implemented._" while as-intended Part II (§11–§14) carries a full global vision, EMT answers, user stories, and per-feature intentions -- several of which are implemented. Only §4 (Workspace Grid, plan-000104) is logged. Metacomm mirroring has fallen behind.

---

## Low-severity / housekeeping

### L1. JM-TB-003 intent vs as-coded selection surface

as-intended JM-TB-003 step 8 anticipates a shared `selectedIds` store feeding a single SelectionBar from map+table. D-013 then supersedes the SelectionBar with the basket. as-coded §8 still documents the SelectionBar (plan-000137) and has not absorbed the D-013 supersession (see H1).

### L2. `D-008` heading has a duplicated title prefix

In as-intended, the heading reads `### D-008: ### D-008: Workspace em grid...` (literal duplication). Cosmetic, but it will confuse any heading-grep tooling.

### L3. as-coded §1 endpoint count label

as-coded §1 says "Nineteen endpoints live" but the enumerated list plus the saved-filter (5) and public-forwarding (3, once H1 is reconciled) endpoints exceed nineteen. The count label drifts as endpoints accrete.

---

## Aligned (no drift)

- Core entities User / ReportType / Report / Forwarding / ForwardingReport -- fields, FKs, soft-delete on ReportType, many-to-many forwarding all match.
- Core permission model: public geojson/report_types, citizen write, agent+admin forwardings, admin report_types CRUD.
- Validation constants (§10 both files) -- text 10–2000, lat/lon bounds, name/institution/solution ranges, JWT 24h, enums.
- JM-TB-001 (citizen registers report) and JM-TB-002 (agent creates forwarding) -- implemented end-to-end, matched in both files.

---

## Recommended sync actions

Ordered by leverage:

1. **Update as-coded for roadmap-000146 (H1)** -- add the public-forwarding endpoints to §1/§4, `author_id` to §2 `ReportFilters`, and the `cesta` view + SelectionBar removal to §8; add a Changelog entry. This is the largest and most mechanical gap. (Agent-maintained file -- safe to write directly.)
2. **Promote Decision markers (H4)** -- apply `STATUS: implemented` to D-007–D-013 via `apply_marker.py` (the only sanctioned write path for the Human (markers) as-intended file). Requires explicit confirmation per file-maintainer rules.
3. **Refresh as-intended §16 and §17 (H2, H3)** -- rewrite the "Conceptual Design Delta" and "Metacommunication Delta" to reflect implemented state. These are prose edits to a Human (markers) file -> propose to the designer; agent must not rewrite prose directly.
4. **Reconcile BERTopic -> TF-IDF (M1, M4)** -- update as-intended §8 / JM-TB-003 wording (designer prose) and fix the as-coded Journey Maps "BERTopic" label.
5. **Anchor orphaned features in intent (M2, M3)** -- add Decision entries (or §2/§4 rows) for SavedFilter, the NL filter, the unified query endpoint, and the admin seed endpoints, or consciously mark them PoC-scaffolding out of scope.
6. **Housekeeping** -- fix the duplicated D-008 heading (L2) and the endpoint-count label (L3).

> Note on write boundaries: `product-design-as-coded.md` is Agent-maintained (post-skill) -- items 1, 4-as-coded, 6-L3 can be written directly. `product-design-as-intended.md` is **Human (markers)** -- STATUS markers go through `apply_marker.py` after explicit confirmation; all prose changes (§16/§17 rewrites, BERTopic wording, new Decision entries, D-008 heading) must be proposed to the designer, not written by the agent.
