"""Tests for scripts/reindex_selfdocs.py — the offline self-docs (re)indexer.

`scripts/` is not a package, so the module is loaded via importlib from its file path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "reindex_selfdocs.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("reindex_selfdocs", _SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mod() -> ModuleType:
    return _load_module()


@pytest.fixture
def tiny_corpus(tmp_path: Path) -> tuple[str, list[str]]:
    """Build a tiny corpus: 1 plan (internal), 1 communication (public), 1 excluded.

    Returns (repo_root, roots) suitable for walk_corpus / tally.
    """
    plans = tmp_path / "_output" / "plans"
    comms = tmp_path / "_output" / "communication"
    design = tmp_path / "product-design" / "project"
    for d in (plans, comms, design):
        d.mkdir(parents=True, exist_ok=True)

    (plans / "plan-000001.md").write_text(
        "# Plan One\n\nThis is an internal plan with some body text.\n",
        encoding="utf-8",
    )
    (comms / "newsletter.md").write_text(
        "# Newsletter\n\nThis is public communication content.\n",
        encoding="utf-8",
    )
    # Excluded sensitive file (matches _EXCLUDE_SUBSTRINGS "security-checklists").
    (design / "security-checklists.md").write_text(
        "# Security Checklists\n\nSensitive content that must never be indexed.\n",
        encoding="utf-8",
    )

    roots = ["_output/plans", "_output/communication", "product-design/project"]
    return (str(tmp_path), roots)


def test_dry_run_tally_counts(mod: ModuleType, tiny_corpus: tuple[str, list[str]]) -> None:
    repo_root, roots = tiny_corpus
    tally = mod.tally_corpus(roots, repo_root)
    assert tally["internal"] == 1
    assert tally["public"] == 1
    assert len(tally["excluded"]) == 1
    assert "security-checklists.md" in tally["excluded"][0]
    assert tally["by_doc_type"].get("plan") == 1
    assert tally["by_doc_type"].get("communication") == 1


def test_if_empty_skips_when_collection_not_empty(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """if_empty=True must short-circuit (no walk, no model load) when count() > 0."""

    class _StubClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def count(self) -> int:
            return 7

        def reindex_all(
            self, chunks: list[Any], *, show_progress: bool = False
        ) -> None:  # pragma: no cover
            raise AssertionError("reindex_all must not be called when skipping")

    walk_called = False

    def _fake_walk(roots: list[str], repo_root: str) -> list[Any]:  # pragma: no cover
        nonlocal walk_called
        walk_called = True
        return []

    monkeypatch.setattr(mod, "ChromaDocSearchClient", _StubClient)
    monkeypatch.setattr(mod, "SentenceTransformer", lambda *a, **k: object())
    monkeypatch.setattr(mod, "walk_corpus", _fake_walk)

    result = mod.index_selfdocs(if_empty=True)
    assert result["skipped"] is True
    assert result["count"] == 7
    assert walk_called is False


def test_index_selfdocs_indexes_when_empty(
    mod: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When collection is empty, walk + reindex run and a summary dict is returned."""

    indexed_chunks: list[Any] = []

    class _Chunk:
        def __init__(self, role: str, doc_type: str) -> None:
            self.role_visibility = role
            self.doc_type = doc_type

    class _StubClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def count(self) -> int:
            return 0

        def reindex_all(
            self, chunks: list[Any], *, show_progress: bool = False
        ) -> None:
            indexed_chunks.extend(chunks)

    fake_chunks = [_Chunk("public", "communication"), _Chunk("internal", "plan")]

    monkeypatch.setattr(mod, "ChromaDocSearchClient", _StubClient)
    monkeypatch.setattr(mod, "SentenceTransformer", lambda *a, **k: object())
    monkeypatch.setattr(mod, "walk_corpus", lambda roots, repo_root: list(fake_chunks))

    result = mod.index_selfdocs()
    assert result["indexed_chunks"] == 2
    assert result["public"] == 1
    assert result["internal"] == 1
    assert result["by_doc_type"]["communication"] == 1
    assert result["by_doc_type"]["plan"] == 1
    assert len(indexed_chunks) == 2
