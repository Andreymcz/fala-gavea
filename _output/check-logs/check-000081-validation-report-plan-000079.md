# Check 000081 | CHOREall | 2026-06-18 13:38 UTC | Validation Report plan-000079

## Scope: all

## Summary

| Check | Status | Issues | Notes |
|-------|--------|--------|-------|
| ruff lint (src/ tests/) | PASS | 0 | 8 errors found and fixed (6 auto-fixed, 2 manual) before report |
| check_conventions | WARN | 18 undefined vars in template files | All in harness template files (.claude/references/template/), not project files — expected for FastAPI-only stack |
| check_vuln_patterns (src/) | PASS | 0 | 1 finding in harness scaffold tool, not project source |
| check_design_output | PASS | 0 | Design output integrity OK |
| check_api_auth_decorators | N/A | — | Script targets Flask/React layout; not applicable to this FastAPI project |
| check_validation_constants_sync | N/A | — | Script targets Flask/React layout; not applicable |
| check_route_coverage | N/A | — | Script targets Flask blueprint routes; not applicable |
| pytest (38 tests) | PASS | 0 | 38/38 tests passed |

## Overall: 4/4 applicable checks passed (3 N/A for FastAPI stack, 0 failures)

## Test Results

```
38 passed, 80 warnings in 32.49s
```

All 13 new forwarding tests pass. Full suite 38/38 green.

Warnings are advisory (httpx deprecation in starlette, JWT key length for test fixture — not production concerns).

## Deferred

- check_api_auth_decorators / check_validation_constants_sync / check_route_coverage: these three plugins target Flask+React layout and are not calibrated for this project's FastAPI+static HTML stack. Consider adding FastAPI-aware equivalents or configuring plugin paths in conventions.md.
- check_conventions 18 undefined vars: all in harness template files authored for multi-stack projects; benign for this single-stack project.
