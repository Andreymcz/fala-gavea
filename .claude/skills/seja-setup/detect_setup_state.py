#!/usr/bin/env python3
# designer: When /seja-setup lands in your directory, I look around
#   first and tell the skill what kind of place it is -- a fresh
#   download, a half-initialised project, a fully configured project,
#   or the SEJA development repo itself -- so the skill can pick the
#   right path and refuse to overwrite something it shouldn't. You see
#   the verdict as a short recommendation, not raw file inventory.
"""detect_setup_state.py -- Inspect the current working directory and report its SEJA setup state.

Invocation: skill-invoked, user-cli
Lifecycle: active

Used by `/seja-setup` to decide whether the current directory is a fresh
download, a partially initialised project, a finalised project, or a SEJA dev repo
(which must refuse in-place setup). Emits a state enum, a structured signals
dictionary, and a short human-readable recommendation.

CLI:
    python detect_setup_state.py [--json] [--cwd <path>]

Library:
    from detect_setup_state import detect_state, State

"""

# Rationale for design choices and historical context: see detect_setup_state-rationale.md in this directory.
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SEJA_PRIV_RE = re.compile(r"(?i)github\.com[:/]simonedjb/seja-priv(\.git)?/?$")
SEJA_PUBLIC_RE = re.compile(r"(?i)github\.com[:/]simonedjb/seja(\.git)?/?$")

DEV_SCRIPT_PATHS = (
    "tools/sync_to_public.py",
    "tools/cut_tag.py",
    "tools/pre_publish_smoke.py",
)

OUTPUT_SIZE_THRESHOLD = 200


class State:
    """String constants for the setup-state enum."""

    NO_HARNESS = "no-harness"
    FRESH_DOWNLOAD = "fresh-download"
    PARTIAL_INIT = "partial-init"
    FINALISED = "finalised"
    DEV_REPO_REFUSE = "dev-repo-refuse"
    PUBLIC_CLONE_SOFT_CONFIRM = "public-clone-soft-confirm"


RECOMMENDATIONS = {
    State.DEV_REPO_REFUSE: (
        "You are in a SEJA development repo. /seja-setup --here is intended for end-user projects."
    ),
    State.NO_HARNESS: (
        "No SEJA harness files here. Use /seja-setup <target> to set up a new project."
    ),
    State.FRESH_DOWNLOAD: (
        "SEJA is downloaded but not finalised. Run /seja-setup --here to initialise setup."
    ),
    State.PARTIAL_INIT: "Setup is partially complete. /seja-setup --here can reconcile.",
    State.FINALISED: (
        "SEJA is already finalised here. Use /seja-setup --upgrade to pull harness updates."
    ),
    State.PUBLIC_CLONE_SOFT_CONFIRM: (
        "This looks like a fresh clone of public SEJA. Confirm you want to turn it "
        "into your project before running /seja-setup --here."
    ),
}


def _run_git(args: list[str], cwd: Path) -> str | None:
    """Run a git subprocess; return stdout stripped, or None on any failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _get_git_remote_url(cwd: Path) -> str | None:
    """Return the origin remote URL, or None if no git repo or no origin."""
    return _run_git(["remote", "get-url", "origin"], cwd)


def _matches_seja_priv(url: str | None) -> bool:
    return bool(url) and bool(SEJA_PRIV_RE.search(url))


def _matches_seja_public(url: str | None) -> bool:
    """True if url points to public simonedjb/seja (and not seja-priv)."""
    if not url:
        return False
    if SEJA_PRIV_RE.search(url):
        return False
    return bool(SEJA_PUBLIC_RE.search(url))


def _has_seja_public_subtree(cwd: Path) -> bool:
    """True if cwd/seja-public/ exists and contains a docs/ directory."""
    subtree = cwd / "seja-public"
    if not subtree.is_dir():
        return False
    return (subtree / "docs").is_dir()


def _present_dev_scripts(cwd: Path) -> list[str]:
    """Return the list of dev-script relative paths that exist under cwd."""
    return [rel for rel in DEV_SCRIPT_PATHS if (cwd / rel).is_file()]


def _head_branch(cwd: Path) -> str | None:
    """Return the current branch name, or None if detached / no git."""
    return _run_git(["symbolic-ref", "--short", "HEAD"], cwd)


def _head_at_default_branch(cwd: Path) -> bool | None:
    """True if HEAD is on main/master with no divergence from origin/<branch>.

    Returns None if any git operation fails (not a git repo, detached HEAD, etc.).
    """
    branch = _head_branch(cwd)
    if branch is None:
        return None
    if branch not in ("main", "master"):
        return False
    # Divergence: count commits ahead of origin/<branch>.
    ahead = _run_git(["rev-list", "--count", f"HEAD..origin/{branch}"], cwd)
    behind = _run_git(["rev-list", "--count", f"origin/{branch}..HEAD"], cwd)
    if ahead is None or behind is None:
        # Can't verify divergence; be conservative and treat as unknown.
        return None
    return ahead == "0" and behind == "0"


def _output_non_empty(output_dir: Path) -> bool:
    """Conservative check: any file >200 bytes, or any subdir with files."""
    if not output_dir.is_dir():
        return False
    for entry in output_dir.rglob("*"):
        if entry.is_file():
            try:
                if entry.stat().st_size > OUTPUT_SIZE_THRESHOLD:
                    return True
            except OSError:
                continue
        # A subdirectory containing any file (checked on subsequent iterations).
    # Second pass: any subdirectory with at least one file inside it.
    for entry in output_dir.iterdir():
        if entry.is_dir():
            for child in entry.rglob("*"):
                if child.is_file():
                    return True
    return False


def _collect_signals(cwd: Path) -> dict:
    """Gather all detection signals without short-circuiting."""
    claude_dir = cwd / ".claude"
    # Accept the merged setup skill directory as the harness-present signal so
    # legacy projects still detect as installed before their first upgrade.
    setup_skill = claude_dir / "skills" / "seja-setup" / "SKILL.md"
    legacy_setup_skill = claude_dir / "skills" / "setup" / "SKILL.md"
    project_dir_new = cwd / "product-design"
    project_dir_pre_rename = cwd / "project-design"  # pre-migration-0003 name
    project_dir_old = cwd / "_references" / "project"
    project_dir = (
        project_dir_new if project_dir_new.is_dir()
        else project_dir_pre_rename if project_dir_pre_rename.is_dir()
        else project_dir_old
    )
    project_conventions_exists = (
        (project_dir_new / "conventions.md").is_file()
        or (project_dir_pre_rename / "conventions.md").is_file()
        or (project_dir_old / "conventions.md").is_file()
    )
    output_dir = cwd / "_output"

    remote_url = _get_git_remote_url(cwd)

    return {
        "has_claude": claude_dir.is_dir(),
        "has_setup_skill": setup_skill.is_file() or legacy_setup_skill.is_file(),
        "has_project_dir": project_dir.is_dir(),
        "has_project_conventions": project_conventions_exists,
        "has_output": output_dir.is_dir(),
        "output_non_empty": _output_non_empty(output_dir),
        "git_remote_url": remote_url,
        "has_seja_public_subtree": _has_seja_public_subtree(cwd),
        "has_dev_scripts": _present_dev_scripts(cwd),
        "head_at_default_branch": _head_at_default_branch(cwd),
    }


def _classify(signals: dict) -> str:
    """Apply the priority-ordered classification rules to the signals dict."""
    remote = signals["git_remote_url"]

    # (a) Dev-repo signals win over everything else.
    dev_repo = (
        _matches_seja_priv(remote)
        or signals["has_seja_public_subtree"]
        or bool(signals["has_dev_scripts"])
    )
    if dev_repo:
        return State.DEV_REPO_REFUSE

    # (b) No setup SKILL.md anywhere => no harness.
    if not signals["has_setup_skill"]:
        return State.NO_HARNESS

    # (c) Public clone soft-confirm: fresh public clone, no project config yet.
    if (
        _matches_seja_public(remote)
        and signals["head_at_default_branch"] is True
        and not signals["has_project_conventions"]
        and not signals["output_non_empty"]
    ):
        return State.PUBLIC_CLONE_SOFT_CONFIRM

    # (d) Finalised: .claude + conventions + populated _output.
    if (
        signals["has_claude"]
        and signals["has_project_conventions"]
        and signals["output_non_empty"]
    ):
        return State.FINALISED

    # (e) Partial init: one of project/output exists but not both (or one empty).
    has_project = signals["has_project_dir"] or signals["has_project_conventions"]
    has_output_populated = signals["has_output"] and signals["output_non_empty"]
    if signals["has_claude"] and (has_project ^ has_output_populated):
        return State.PARTIAL_INIT
    if (
        signals["has_claude"]
        and signals["has_output"]
        and not signals["output_non_empty"]
        and has_project
    ):
        # Output exists but empty + project configured => partial.
        return State.PARTIAL_INIT

    # (f) Fallback: just .claude, no project config, no meaningful output.
    return State.FRESH_DOWNLOAD


def detect_state(cwd: Path) -> dict:
    """Inspect ``cwd`` and return a dict with state, signals, and recommendation.

    Raises FileNotFoundError if ``cwd`` does not exist. Does not raise on any
    subordinate failure (missing git binary, detached HEAD, etc.) -- those
    conditions are reflected as None in the signals dict.
    """
    if not cwd.exists():
        raise FileNotFoundError(f"cwd does not exist: {cwd}")
    signals = _collect_signals(cwd)
    # Trim the internal-only signals before emitting the JSON shape.
    public_signals = {
        "has_claude": signals["has_claude"],
        "has_project_conventions": signals["has_project_conventions"],
        "has_output": signals["has_output"],
        "output_non_empty": signals["output_non_empty"],
        "git_remote_url": signals["git_remote_url"],
        "has_seja_public_subtree": signals["has_seja_public_subtree"],
        "has_dev_scripts": signals["has_dev_scripts"],
        "head_at_default_branch": signals["head_at_default_branch"],
    }
    state = _classify(signals)
    return {
        "state": state,
        "signals": public_signals,
        "recommendation": RECOMMENDATIONS[state],
    }


def _format_human(result: dict) -> str:
    lines = [
        f"state: {result['state']}",
        f"recommendation: {result['recommendation']}",
        "signals:",
    ]
    for key, value in result["signals"].items():
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect the SEJA setup state of a directory."
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="Directory to inspect (default: current working directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    args = parser.parse_args(argv)

    cwd = Path(args.cwd) if args.cwd else Path.cwd()
    if not cwd.exists():
        print(f"ERROR: cwd does not exist: {cwd}", file=sys.stderr)
        return 2

    result = detect_state(cwd)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(_format_human(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
