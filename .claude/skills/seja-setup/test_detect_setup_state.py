#!/usr/bin/env python3
# designer: When /seja-setup inspects a directory to decide whether it is a fresh
#   download, a partially initialised project, a finalised one, or the SEJA
#   dev repo itself, I'm the test suite that pins each of those verdicts
#   against a fixture directory. You get confidence that the state-detection
#   logic keeps returning the right enum for the right shape, so /seja-setup does
#   not one day agree to seed into a directory it should have refused.
"""test_detect_setup_state.py -- Tests for detect_setup_state.py.

Invocation: test
Lifecycle: active

Covers each State enum value via tempdir fixtures. See plan-000392 step 1,
plan-000406 step 5 (rename /seed to /setup), and plan-000433 step 13 (merge
/setup + /upgrade into /seja-setup).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from detect_setup_state import State, detect_state, main  # noqa: E402


# ---------- Fixture helpers --------------------------------------------------


def make_claude_skills(tmpdir: Path) -> None:
    """Create a minimal .claude/skills/seja-setup/SKILL.md under tmpdir.

    Post plan-000433, the merged skill directory is `seja-setup/`. The
    detector also accepts a legacy `setup/` directory for backward-compat
    with projects that have not yet upgraded.
    """
    skill_dir = tmpdir / ".claude" / "skills" / "seja-setup"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: seja-setup\n---\n# seja-setup skill placeholder\n",
        encoding="utf-8",
    )


def make_project_conventions(tmpdir: Path) -> None:
    """Create product-design/conventions.md with minimal content (new layout)."""
    project_dir = tmpdir / "product-design"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "conventions.md").write_text(
        "# project conventions\n\nMinimal.\n", encoding="utf-8"
    )


def make_project_conventions_legacy(tmpdir: Path) -> None:
    """Create _references/project/conventions.md with minimal content (legacy layout)."""
    project_dir = tmpdir / "_references" / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "conventions.md").write_text(
        "# project conventions\n\nMinimal.\n", encoding="utf-8"
    )


def make_populated_output(tmpdir: Path) -> None:
    """Create _output/briefs.md (>500 bytes) and _output/plans/ subdir with a file."""
    output = tmpdir / "_output"
    output.mkdir(parents=True, exist_ok=True)
    briefs_body = "# briefs\n\n" + ("some content line.\n" * 40)
    assert len(briefs_body) > 500
    (output / "briefs.md").write_text(briefs_body, encoding="utf-8")
    plans = output / "plans"
    plans.mkdir(exist_ok=True)
    (plans / "plan-000000.md").write_text("# plan placeholder\n", encoding="utf-8")


def init_git_with_remote(
    tmpdir: Path, url: str | None = None, branch: str = "main"
) -> None:
    """git init + optional remote + an initial commit on the given branch."""
    env_args = {
        "cwd": str(tmpdir),
        "capture_output": True,
        "text": True,
        "check": True,
    }
    subprocess.run(["git", "init", "-b", branch], **env_args)
    subprocess.run(["git", "config", "user.email", "t@test"], **env_args)
    subprocess.run(["git", "config", "user.name", "tester"], **env_args)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], **env_args)
    if url is not None:
        subprocess.run(["git", "remote", "add", "origin", url], **env_args)
    # Create an initial commit so HEAD resolves.
    (tmpdir / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", ".gitkeep"], **env_args)
    subprocess.run(
        ["git", "commit", "-m", "init", "--no-gpg-sign"], **env_args
    )


# ---------- Tests ------------------------------------------------------------


def test_no_harness_empty_dir():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        result = detect_state(tmp)
        assert result["state"] == State.NO_HARNESS


def test_no_harness_with_git_only():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_git_with_remote(tmp, url=None)
        result = detect_state(tmp)
        assert result["state"] == State.NO_HARNESS


def test_fresh_download():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        (tmp / "_references").mkdir(exist_ok=True)
        result = detect_state(tmp)
        assert result["state"] == State.FRESH_DOWNLOAD
        assert result["signals"]["has_claude"] is True
        assert result["signals"]["has_project_conventions"] is False


def test_partial_init_project_only():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        make_project_conventions(tmp)
        result = detect_state(tmp)
        assert result["state"] == State.PARTIAL_INIT


def test_partial_init_output_only():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        make_populated_output(tmp)
        result = detect_state(tmp)
        assert result["state"] == State.PARTIAL_INIT


def test_finalised():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        make_project_conventions(tmp)
        make_populated_output(tmp)
        result = detect_state(tmp)
        assert result["state"] == State.FINALISED


def test_dev_repo_seja_public_subtree():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        make_project_conventions(tmp)
        make_populated_output(tmp)
        # Add a seja-public/ subtree with a docs/ inside.
        (tmp / "seja-public" / "docs").mkdir(parents=True)
        result = detect_state(tmp)
        assert result["state"] == State.DEV_REPO_REFUSE
        assert result["signals"]["has_seja_public_subtree"] is True


def test_dev_repo_sync_script():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        tools = tmp / "tools"
        tools.mkdir()
        (tools / "sync_to_public.py").write_text(
            "# placeholder\n", encoding="utf-8"
        )
        result = detect_state(tmp)
        assert result["state"] == State.DEV_REPO_REFUSE
        assert "tools/sync_to_public.py" in result["signals"]["has_dev_scripts"]


def test_dev_repo_remote_seja_priv():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_git_with_remote(
            tmp, url="https://github.com/simonedjb/seja-priv.git"
        )
        make_claude_skills(tmp)
        result = detect_state(tmp)
        assert result["state"] == State.DEV_REPO_REFUSE


def test_public_clone_soft_confirm():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        init_git_with_remote(
            tmp, url="https://github.com/simonedjb/seja.git", branch="main"
        )
        make_claude_skills(tmp)
        # No remote branch exists, so head_at_default_branch may be None
        # (rev-list HEAD..origin/main will fail). Simulate a pushed state by
        # creating a local ref that mirrors origin/main.
        subprocess.run(
            [
                "git",
                "update-ref",
                "refs/remotes/origin/main",
                "HEAD",
            ],
            cwd=str(tmp),
            check=True,
            capture_output=True,
        )
        result = detect_state(tmp)
        assert result["state"] == State.PUBLIC_CLONE_SOFT_CONFIRM


def test_cwd_does_not_exist():
    """detect_state on a nonexistent path raises FileNotFoundError."""
    bogus = Path(tempfile.gettempdir()) / "definitely-not-a-real-seja-dir-xyz123"
    if bogus.exists():
        pytest.skip("pre-existing path collision; re-run in clean env")
    with pytest.raises(FileNotFoundError):
        detect_state(bogus)


def test_json_output_shape():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        result = detect_state(tmp)
        assert set(result.keys()) == {"state", "signals", "recommendation"}
        expected_signal_keys = {
            "has_claude",
            "has_project_conventions",
            "has_output",
            "output_non_empty",
            "git_remote_url",
            "has_seja_public_subtree",
            "has_dev_scripts",
            "head_at_default_branch",
        }
        assert set(result["signals"].keys()) == expected_signal_keys
        # Round-trip through JSON to ensure the shape is serialisable.
        round_trip = json.loads(json.dumps(result))
        assert round_trip["state"] == result["state"]


def test_cli_exit_code_zero(capsys):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        rc = main(["--cwd", str(tmp), "--json"])
        assert rc == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload["state"] == State.FRESH_DOWNLOAD


def test_cli_exit_code_two_for_missing_cwd(capsys):
    bogus = Path(tempfile.gettempdir()) / "definitely-not-a-real-seja-dir-xyz456"
    if bogus.exists():
        pytest.skip("pre-existing path collision; re-run in clean env")
    rc = main(["--cwd", str(bogus)])
    assert rc == 2


def test_finalised_legacy_layout():
    """FINALISED is detected when conventions.md lives under _references/project/ (legacy layout)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        make_claude_skills(tmp)
        make_project_conventions_legacy(tmp)
        make_populated_output(tmp)
        result = detect_state(tmp)
        assert result["state"] == State.FINALISED
        assert result["signals"]["has_project_conventions"] is True
