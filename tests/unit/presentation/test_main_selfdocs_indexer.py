"""Tests for the background self-docs indexer launched at app startup.

The indexer runs in a daemon thread and must NEVER raise out of startup
(a missing corpus, a broken module load, or an indexing failure must not
take the API down). These tests exercise `_launch_selfdocs_indexer` directly.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from fala_gavea.presentation.api import main


def test_launch_selfdocs_indexer_swallows_load_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failure loading the indexer module must be swallowed, not raised."""

    def _boom(*args: object, **kwargs: object) -> object:
        raise RuntimeError("import blew up")

    # Force the importlib path to raise after the script-exists check passes.
    monkeypatch.setattr(main.Path, "exists", lambda self: True)
    monkeypatch.setattr(importlib.util, "spec_from_file_location", _boom)

    # Must not raise.
    main._launch_selfdocs_indexer()


def test_launch_selfdocs_indexer_skips_when_script_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the script is absent, the indexer skips quietly (no exception)."""
    monkeypatch.setattr(main.Path, "exists", lambda self: False)

    called = False

    def _should_not_run(*args: object, **kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("must not attempt to load module when script missing")

    monkeypatch.setattr(importlib.util, "spec_from_file_location", _should_not_run)

    main._launch_selfdocs_indexer()
    assert called is False


def test_repo_root_depth_resolves_to_scripts_dir() -> None:
    """Confirm parents[4] from main.py points at the repo root holding scripts/."""
    repo_root = Path(main.__file__).resolve().parents[4]
    assert (repo_root / "scripts").is_dir()
    assert (repo_root / "scripts" / "reindex_selfdocs.py").is_file()
