# QA Log -- plan-000131 | Refine data exploration search filters

source: plan-000131
brief: Implement research-000129 recommendations (staged filter + Apply button, Tipos routing-bug fix, date presets, table sort/full-text, map filter-this-area, regression tests).

## Decision Q&A

**Q1: How to proceed with the research-000129 recommendations?**
A1: Plan now (all 5 recommendations).

**Q2: For the staged filter (R1), which model should the plan target -- full Apply button, Apply + debounce, or debounce + chips only?**
A2: Full Apply button. (Note recorded in plan: with a full Apply button the semantic query becomes part of the draft and fires only on Apply, so a separate debounce is unnecessary.)

**Q3: Record the staged-filter decision as D-009 in product-design-as-intended.md?**
A3: Create now. D-009 ("Filtro encenado (draft + Aplicar) substitui o cross-filtering ao vivo do D-008") appended via apply_marker.py (DECISION_APPEND).

## Notes / surprises

- The Tipos combobox bug (R2) was confirmed as a production-only routing defect: the SPA catch-all `@app.get("/{full_path:path}")` shadows the slashless `GET /report_types` 307 redirect and returns `index.html`, so the client parses HTML and the list silently empties. Invisible in `npm run dev` (no static dir); same latent defect affects `GET /forwardings`.
- This harness copy is missing some scripts (`generate_decision_digest.py`, `check_docs.py`, `check_spec_conformance.py`) and the `_internal/plan/standard/SKILL.md`; the standard plan workflow was executed inline. Non-blocking.
