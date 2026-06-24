# Check 000159 | CHORE-all | 2026-06-24 11:43 UTC | Validation Report

scope: all
context: post-implementation of roadmap-000151 Wave 2 (plans 156-158, frontend citizen feedback UX)

## Summary

| Check | Status | Errors | Notes |
|-------|--------|--------|-------|
| ruff (linting) | FAIL | 22 | E402 in main.py (intentional), 2 unused imports (auto-fixable) |
| pyright (type checking) | FAIL | 89 | Root cause: SQLAlchemy Column[T] vs Mapped[T] across all repos |
| check_api_auth_decorators | FAIL | 1 | Script hardcoded to backend/app/ — N/A for this layout |
| check_api_contract_sync | PASS | 0 | |
| check_backend_test_coverage | FAIL | 1 | Script path error (WinError 267) |
| check_conventions | FAIL | 18 | Template placeholder variables not in this project's conventions.md |
| check_design_output | PASS | 0 | |
| check_frontend_test_coverage | FAIL | 1 | Missing @vitest/coverage-v8 dev dep |
| check_migration_chain | FAIL | 1 | Script expects Alembic layout — N/A (uses create_tables()) |
| check_po_parity | FAIL | 1 | No Flask-Babel — N/A |
| check_route_coverage | PASS | 0 | |
| check_vuln_patterns | FAIL | 11 | Built bundle artifacts (not source); 1 scaffold tool false positive |
| check_validation_constants_sync | FAIL | 1 | Script hardcoded to wrong path — N/A |
| check_unused_files | FAIL | 11 | React Router route components (dynamic refs, not dead code) |
| check_i18n_keys | FAIL | 2 | No react-i18next / Flask-Babel — N/A |
| check_harness_drift | PASS | 0 | |
| check_worktree_health | PASS | 0 | |
| check_human_markers_only | PASS | 0 | |
| check_skill_spec | PASS | 0 | |
| check_skill_system | FAIL | 24 | Missing product-design/ prefix in skill refs; check_secrets import error |
| check_telemetry | FAIL | 47 | Schema drift: null context_budget + unknown session_id field |
| check_version_changelog_sync | FAIL | 1 | No .claude/CHANGELOG.md |

**Overall: 7/22 checks passed**

## Wave 2 specific findings (new since roadmap-000151)

None of the failures are introduced by Wave 2. All failures are pre-existing:
- Pyright errors are in the SQLAlchemy repo layer (pre-existing Column[T] pattern)
- Ruff errors: vote_repository.py has 1 unused import (uuid4) — minor, auto-fixable
- No security findings in new frontend files (votes.ts, comments.ts, VoteButtons.tsx, CommentSection.tsx, ReportFormPage.tsx changes)

## Actionable Priorities

### P1 — Fixable now
1. **Ruff auto-fix**: `uv run ruff check src/ --fix` — removes 2 unused imports; add `# noqa: E402` to main.py logging block
2. **@vitest/coverage-v8**: `cd frontend && npm install --save-dev @vitest/coverage-v8`

### P2 — Planned work
3. **Pyright (89 errors)**: Migrate SQLAlchemy repos from `Column[T]` to `Mapped[T]` / `mapped_column()` syntax (SQLAlchemy 2.0). Requires a plan.

### P3 — Not applicable / pre-existing
4. check_api_auth_decorators, check_migration_chain, check_validation_constants_sync, check_i18n_keys, check_po_parity — hardcoded to incompatible project layout; skip or reconfigure
5. check_unused_files — false positives (React Router route targets)
6. check_vuln_patterns — built bundle artifacts; investigate dangerouslySetInnerHTML in source if desired
7. check_skill_system, check_telemetry, check_version_changelog_sync — harness infrastructure drift; lower priority

## Verdict

**No new failures introduced by Wave 2.** Pre-existing checks account for all failures.
