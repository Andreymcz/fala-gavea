# QA Log | plan-000137 | 2026-06-21 19:58 UTC | Phase A extended panel draft filters table

## Brief

Phase A: extended plan-000131 — four-section left panel (w-72, collapsible, preset bar + active chips + draft controls + NL assistant footer placeholder), staged draft/Apply model with loadedPresetName + draftFilterName + draft-loss guard, date presets, SPA routing fix, TableView sort + Radix Dialog full-text + pagination + score column + density toggle, MapView filter-this-area. source: research-000136 + research-000129 + plan-000131

## Q&A

**Q1:** Plan Phase A of the UI overhaul: four-section left panel, staged draft/Apply model, date presets, SPA routing fix, TableView improvements, MapView "Filtrar nesta área". Source: research-000136 + research-000129 + plan-000131 (superseded).

**A1:** Plan-000137 produced with 8 steps. Supersedes plan-000131 (same scope extended with four-section layout from research-000136). Key decisions: `isDirty()` must use `get()` internally to avoid stale-closure pitfalls; sort `<th>` uses inner `<button>` pattern for WAI-ARIA keyboard operability; score column includes `sr-only` band text for WCAG 1.4.1; sort config change resets pagination to page 0; bbox commits immediately to both slices (direct manipulation, no Apply required). Section 4 NL assistant scaffolded as a disabled placeholder; Sections 1 (preset bar) left as visible but disabled stubs for Phase B wiring.
