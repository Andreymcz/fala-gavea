from __future__ import annotations

import pytest

from fala_gavea.infrastructure.embeddings.registry import (
    _DEFAULT_ROOTS,
    SemanticConfig,
    _split_roots,
)


def test_selfdocs_collection_default() -> None:
    config = SemanticConfig()
    assert config.selfdocs_collection == "falagavea_selfdocs"


def test_selfdocs_collection_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_SELFDOCS_COLLECTION", "custom_selfdocs")
    config = SemanticConfig()
    assert config.selfdocs_collection == "custom_selfdocs"


def test_selfdocs_corpus_roots_default_is_five_paths() -> None:
    config = SemanticConfig()
    assert config.selfdocs_corpus_roots == _DEFAULT_ROOTS
    assert len(config.selfdocs_corpus_roots) == 5


def test_selfdocs_corpus_roots_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_SELFDOCS_ROOTS", "a,b")
    config = SemanticConfig()
    assert config.selfdocs_corpus_roots == ["a", "b"]


def test_selfdocs_corpus_roots_env_empty_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FALA_GAVEA_SELFDOCS_ROOTS", "")
    config = SemanticConfig()
    assert config.selfdocs_corpus_roots == _DEFAULT_ROOTS


def test_split_roots_trims_and_drops_empty() -> None:
    assert _split_roots(" a , b ,, c ,") == ["a", "b", "c"]
    assert _split_roots("") == []
    assert _split_roots("   ") == []


def test_selfdocs_vectorstore_path_explicit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_SELFDOCS_PATH", "/app/selfdocs_chroma")
    config = SemanticConfig()
    assert config.selfdocs_vectorstore_path == "/app/selfdocs_chroma"


def test_selfdocs_vectorstore_path_falls_back_to_chroma_data_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FALA_GAVEA_SELFDOCS_PATH", raising=False)
    monkeypatch.setenv("CHROMA_DATA_DIR", "/data")
    config = SemanticConfig()
    # With no dedicated self-docs path, it shares the reports store path.
    assert config.selfdocs_vectorstore_path == "/data"
    assert config.vectorstore_path == "/data"
