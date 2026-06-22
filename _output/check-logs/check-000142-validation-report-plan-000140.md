# Check 000142 | CHOREall | 2026-06-22 11:58 UTC | Validation Report

## Scope: all

## Summary Table

| Check | Status | Errors | Warnings | Notes |
|-------|--------|--------|----------|-------|
| check_api_auth_decorators | FAIL | 1 | 0 | Path mismatch (pre-existing) |
| check_api_contract_sync | PASS | 0 | 0 | |
| check_backend_test_coverage | FAIL | 1 | 0 | Path mismatch (pre-existing) |
| check_conventions | FAIL | 18 | 18 | Template placeholders (pre-existing) |
| check_design_output | PASS | 0 | 0 | |
| check_frontend_test_coverage | FAIL | 1 | 0 | Missing @vitest/coverage-v8 (pre-existing) |
| check_harness_drift | PASS | 0 | 0 | |
| check_human_markers_only | PASS | 0 | 0 | |
| check_i18n_keys | FAIL | 2 | 0 | Locale files not created (pre-existing) |
| check_migration_chain | FAIL | 1 | 0 | Path mismatch (pre-existing) |
| check_po_parity | FAIL | 1 | 0 | FastAPI project, no Flask-Babel (pre-existing) |
| check_route_coverage | PASS | 0 | 0 | |
| check_skill_spec | PASS | 0 | 0 | |
| check_skill_system | FAIL | 24 | 1 | Missing product-design files (pre-existing) |
| check_telemetry | FAIL | 39 | 18 | context_budget null (pre-existing) |
| check_unused_files | FAIL | 10 | 0 | Router page components (false positive) |
| check_validation_constants_sync | FAIL | 1 | 0 | Path mismatch (pre-existing) |
| check_version_changelog_sync | FAIL | 1 | 0 | Harness CHANGELOG not initialized (pre-existing) |
| check_vuln_patterns | FAIL | 11 | 0 | Built bundle/vendored code + harness SSTI (pre-existing) |
| check_worktree_health | FAIL | 1 | 0 | Git submodule treated as orphaned worktree (pre-existing) |

**Overall: 6/20 checks passed**

## Plan-000140-Relevant Checks

All checks directly relevant to the changes in plan 000140 (NL filter parser backend + NL assistant UX) **PASS**:
- check_api_contract_sync: PASS
- check_design_output: PASS
- check_harness_drift: PASS
- check_human_markers_only: PASS
- check_route_coverage: PASS
- check_skill_spec: PASS

## Pre-existing Failures (not introduced by plan 000140)

All 14 failing checks are pre-existing infrastructure issues:
1. **Path mismatch checks** (auth_decorators, backend_test_coverage, migration_chain, validation_constants_sync): scripts expect `backend/app/` layout; project uses `src/fala_gavea/`.
2. **Flask-Babel checks** (i18n_keys, po_parity): project uses FastAPI, not Flask-Babel.
3. **Template placeholders** (conventions): undefined template variables in harness reference files.
4. **Coverage tooling** (frontend_test_coverage): missing `@vitest/coverage-v8` dependency.
5. **Harness issues** (skill_system, telemetry, version_changelog_sync): pre-existing harness configuration gaps.
6. **False positives** (unused_files): React Router page components are not statically imported.
7. **Bundle scan** (vuln_patterns): findings in minified/vendored third-party code (react-leaflet, shadcn); harness SSTI in scaffold tooling (not project code).
8. **Worktree** (worktree_health): git submodule entry treated as orphaned worktree.
