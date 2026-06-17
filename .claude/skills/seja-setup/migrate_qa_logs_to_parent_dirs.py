#!/usr/bin/env python3
# designer: When a harness upgrade changes where post-skill QA logs
#   belong -- next to the parent artifact instead of pooled under
#   `_output/qa-logs/` -- I'm the one-shot migrator that finds the
#   post-skill companion files, moves each one to sit beside the artifact
#   it documents, and leaves standalone user-invoked QA logs where they
#   were; run with `--apply` to execute or without it to see the dry-run
#   preview first.
"""
migrate_qa_logs_to_parent_dirs.py -- Move post-skill QA logs to parent artifact dirs.

Invocation: skill-invoked, user-cli
Lifecycle: one-shot

Post-skill QA logs (for example, <artifact-id>-qa-*.md) belong next to the artifact
they document, not in the centralized QA_LOGS_DIR. Standalone user-invoked QA
logs (qa-NNNNNN-*.md) remain in QA_LOGS_DIR.

Usage:
    python .claude/skills/seja-setup/migrate_qa_logs_to_parent_dirs.py          # dry-run
    python .claude/skills/seja-setup/migrate_qa_logs_to_parent_dirs.py --apply  # execute

Run from the repository root.
"""

# Rationale for design choices and historical context: see migrate_qa_logs_to_parent_dirs-rationale.md in this directory.
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Shared scripts (project_config, etc.) live in the sibling scripts/ directory
import sys as _sys; from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / 'scripts'))
del _sys, _Path
from project_config import REPO_ROOT, get_path

QA_LOGS_DIR = get_path("QA_LOGS_DIR") or REPO_ROOT / "_output" / "qa-logs"

_STANDALONE_RE = re.compile(r"^qa-\d{4,6}-.*\.(md|txt)$")
_POSTSKILL_RE = re.compile(r"^(?P<prefix>[a-z](?:[a-z-]*[a-z])?)-\d{6}-qa-.*\.md$")
_NOID_RE = re.compile(r"^(?P<prefix>[a-z](?:[a-z-]*[a-z])?)-qa-.*\.md$")

PREFIX_TO_VAR: dict[str, str] = {
    "plan": "PLANS_DIR",
    "implement": "PLANS_DIR",
    "advisory": "ADVISORY_DIR",
    "research": "RESEARCH_DIR",
    "check": "CHECK_LOGS_DIR",
    "proposal": "PROPOSALS_DIR",
    "roadmap": "ROADMAP_DIR",
    "onboarding": "ONBOARDING_PLANS_DIR",
    "communication": "COMMUNICATION_DIR",
    "inventory": "INVENTORIES_DIR",
    "reflection": "REFLECTIONS_DIR",
    "user-tests": "USER_TESTS_DIR",
    "explained-behavior": "EXPLAINED_BEHAVIORS_DIR",
    "explained-code": "EXPLAINED_CODE_DIR",
    "explained-data-model": "EXPLAINED_DATA_MODEL_DIR",
    "explained-architecture": "EXPLAINED_ARCHITECTURE_DIR",
    "behavior-evolution": "BEHAVIOR_EVOLUTION_DIR",
}


def classify(filename: str) -> tuple[str, Path | None]:
    """Classify a QA log file.

    Returns (action, destination_dir) where action is one of:
    - "standalone": user-invoked QA log, skip
    - "move": post-skill QA log with known prefix, move to destination_dir
    - "leave": no-ID post-skill log, leave in place
    - "unknown": unrecognized shape, skip
    - "unknown-prefix": recognized pattern but prefix not in table
    """
    if _STANDALONE_RE.match(filename):
        return "standalone", None

    m = _POSTSKILL_RE.match(filename)
    if m:
        prefix = m.group("prefix")
        var = PREFIX_TO_VAR.get(prefix)
        if var is None:
            return "unknown-prefix", None
        dest = get_path(var)
        if dest is None:
            return "unknown-prefix", None
        return "move", dest

    if _NOID_RE.match(filename):
        return "leave", None

    return "unknown", None


def run(apply: bool = False) -> int:
    if not QA_LOGS_DIR.is_dir():
        print(f"QA logs directory not found: {QA_LOGS_DIR}")
        return 1

    files = sorted(f for f in QA_LOGS_DIR.iterdir() if f.is_file())
    moves: list[tuple[Path, Path]] = []
    skipped_standalone = 0
    skipped_leave = 0
    warnings: list[str] = []

    for fpath in files:
        action, dest_dir = classify(fpath.name)
        if action == "standalone":
            skipped_standalone += 1
        elif action == "move":
            assert dest_dir is not None
            dest = dest_dir / fpath.name
            if dest.exists():
                warnings.append(f"SKIP (exists): {fpath.name} -> {dest}")
            else:
                moves.append((fpath, dest))
        elif action == "leave":
            skipped_leave += 1
            warnings.append(f"LEAVE (no-ID shape): {fpath.name}")
        elif action == "unknown-prefix":
            known = ", ".join(sorted(PREFIX_TO_VAR.keys()))
            warnings.append(
                f"SKIP (unknown prefix): {fpath.name} "
                f"-- extracted prefix not in known list: {known}. "
                f"Add the prefix to post-skill/SKILL.md step 3 if needed."
            )
        else:
            warnings.append(f"SKIP (unrecognized): {fpath.name}")

    print(f"QA logs directory: {QA_LOGS_DIR}")
    print(f"Total files:       {len(files)}")
    print(f"Standalone (skip): {skipped_standalone}")
    print(f"No-ID (leave):     {skipped_leave}")
    print(f"To move:           {len(moves)}")
    print()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  {w}")
        print()

    if not moves:
        print("Nothing to migrate.")
        return 0

    if not apply:
        print("Planned moves (dry-run):")
        for src, dst in moves:
            print(f"  {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
        print(f"\nRun with --apply to execute {len(moves)} moves.")
        return 0

    print("Executing moves:")
    ok = 0
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "mv", str(src), str(dst)],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            ok += 1
            print(f"  OK: {src.name} -> {dst.relative_to(REPO_ROOT)}")
        except subprocess.CalledProcessError as e:
            print(f"  FAIL: {src.name} -- {e.stderr.strip()}")
            print(f"Aborting after {ok} successful moves. Remaining: {len(moves) - ok}")
            return 1

    print(f"\nMigrated {ok} files.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate post-skill QA logs to parent dirs")
    parser.add_argument("--apply", action="store_true", help="Execute moves (default: dry-run)")
    args = parser.parse_args()
    sys.exit(run(apply=args.apply))


if __name__ == "__main__":
    main()
