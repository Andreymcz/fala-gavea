# Check 000106 | CHOREall | 2026-06-19 22:18 UTC | Validation Report — plan-000104

## Scope
`all` — post-implementation validation for plan-000104 (workspace grid + cross-filter + IA widgets)

## Summary

| Check | Status | Errors | Warnings | Notes |
|-------|--------|--------|----------|-------|
| check_api_auth_decorators | FAIL | 1 | 0 | Pre-existing: expects `backend/app/api` path; project uses `src/fala_gavea/` |
| check_api_contract_sync | PASS | 0 | 0 | |
| check_backend_test_coverage | FAIL | 1 | 0 | Pre-existing: path mismatch (expects `backend/`) |
| check_conventions | FAIL | 18 | 18 | Pre-existing: missing template vars in conventions.md |
| check_design_output | PASS | 0 | 0 | |
| check_frontend_test_coverage | FAIL | 1 | 0 | Pre-existing: `@vitest/coverage-v8` not installed |
| check_harness_drift | PASS | 0 | 0 | |
| check_human_markers_only | PASS | 0 | 0 | |
| check_i18n_keys | FAIL | 2 | 0 | Pre-existing: i18n not in scope for this project |
| check_migration_chain | FAIL | 1 | 0 | Pre-existing: path mismatch |
| check_po_parity | FAIL | 1 | 0 | Pre-existing: Flask-Babel not applicable |
| check_route_coverage | PASS | 0 | 0 | |
| check_skill_spec | PASS | 0 | 0 | |
| check_skill_system | FAIL | 24 | 1 | Pre-existing: missing project reference files |
| check_telemetry | FAIL | 18 | 27 | Pre-existing: schema drift in telemetry records |
| check_unused_files | FAIL | 0 | 9 | Advisory: React Router pages flagged; expected pattern |
| check_validation_constants_sync | FAIL | 1 | 0 | Pre-existing: path mismatch |
| check_version_changelog_sync | FAIL | 1 | 0 | Pre-existing: no harness CHANGELOG.md |
| check_vuln_patterns | FAIL | 11 | 0 | Bundled/vendor assets; no first-party findings in diff |
| check_worktree_health | FAIL | 1 | 0 | 1 orphaned worktree from prior parallel execution |

**Overall: 6/20 checks passed**

## Assessment

All failures are **pre-existing** infrastructure mismatches (path conventions don't match project layout, i18n not applicable, missing conventions.md variables). No new failures introduced by plan-000104. The `check_vuln_patterns` findings are all in compiled/vendored bundles (`static/assets/`), not in first-party source code introduced by this plan.

Frontend tests: 28/28 passing. Build: clean (263 modules, no TypeScript errors).
