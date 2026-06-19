# Check 000093 | CHORE-all | 2026-06-19 14:02 UTC | Validation Report

## Scope: all

## Summary

| Check | Status | Errors | Warnings | Notes |
|-------|--------|--------|----------|-------|
| conventions | FAIL | 18 | 18 | Undefined template vars in `.claude/references/template/` (harness-side, not project code) |
| api_auth_decorators | FAIL | 1 | 0 | Path mismatch — expects `backend/app/api/`, project uses `src/fala_gavea/` |
| api_contract_sync | INFO | 0 | 0 | No KNOWN_PAIRS configured; no-op |
| backend_test_coverage | FAIL | 1 | 0 | Script hardcodes `backend/` dir; does not match `src/fala_gavea/` |
| design_output | PASS | 0 | 0 | |
| frontend_test_coverage | FAIL | 1 | 0 | `npx` not on PATH; coverage JSON missing |
| harness_drift | INFO | 0 | 0 | Skipped — no `--source` flag provided |
| human_markers_only | PASS | 0 | 0 | 0 Human-marker files found |
| i18n_keys | FAIL | 2 | 0 | i18n not applicable (FastAPI, not Flask-Babel) |
| migration_chain | FAIL | 1 | 0 | No Alembic versions dir; SQLAlchemy direct |
| po_parity | FAIL | 1 | 0 | Flask-Babel .po not applicable (FastAPI) |
| route_coverage | FAIL | 2 | 0 | Hardcoded paths do not match project layout |
| skill_spec | PASS | 0 | 0 | All 18 skills comply |
| skill_system | FAIL | 24 | 1 | Missing some product-design files; invalid skill category |
| telemetry | FAIL | 10 | 14 | `context_budget` null in 10/14 records |
| unused_files | INFO | 0 | 0 | 9 possibly orphaned frontend files (router-loaded) |
| validation_constants_sync | FAIL | 1 | 0 | Wrong project layout |
| version_changelog_sync | FAIL | 1 | 0 | `.claude/CHANGELOG.md` absent |
| vuln_patterns | FAIL | 1 | 0 | [HIGH] SSTI in `.claude/skills/python-scaffold/scripts/scaffold.py:43` |
| worktree_health | FAIL | 1 | 0 | Orphaned worktree at `E:/dev/inf2921-grupo-c/.git/modules/fala-gavea` |

**Overall: 4/20 checks passed** (+ 3 INFO/non-blocking)

## Categorisation

### Path misconfiguration (harness template defaults — not code defects)
Scripts below assume Flask/generic template layout (`backend/app/api/`) rather than this project's `src/fala_gavea/` structure. Failures are false positives:
- `api_auth_decorators`, `backend_test_coverage`, `migration_chain`, `po_parity`, `route_coverage`, `validation_constants_sync`, `i18n_keys`

### Real defects to address

| Priority | Issue | File | Action |
|----------|-------|------|--------|
| HIGH | SSTI risk in scaffold script | `.claude/skills/python-scaffold/scripts/scaffold.py:43` | Fix Jinja2 template injection |
| MEDIUM | Orphaned git worktree | `.git` | `git worktree prune` |
| LOW | `context_budget` null in telemetry | `_output/conversation-trace.jsonl` | Build_telemetry.py fix |
| LOW | `version_changelog_sync` | `.claude/CHANGELOG.md` | Create CHANGELOG |
| LOW | skill_system: invalid category | `python-scaffold/SKILL.md` | Fix `scaffolding` -> valid category |

### Application code: CLEAN
No failures in application source (`src/fala_gavea/`, `tests/`, `scripts/`). All 53 tests pass.
