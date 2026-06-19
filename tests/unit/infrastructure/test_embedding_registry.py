import os

import pytest

from fala_gavea.infrastructure.embeddings.registry import EmbeddingProviderRegistry, SemanticConfig


def test_default_search_model() -> None:
    reg = EmbeddingProviderRegistry(SemanticConfig())
    assert reg.get_model_name("search") == "intfloat/multilingual-e5-base"


def test_default_topics_model() -> None:
    reg = EmbeddingProviderRegistry(SemanticConfig())
    assert reg.get_model_name("topics") == "paraphrase-multilingual-MiniLM-L12-v2"


def test_rag_same_as_search_by_default() -> None:
    reg = EmbeddingProviderRegistry(SemanticConfig())
    assert reg.get_model_name("rag") == reg.get_model_name("search")


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FALA_GAVEA_EMBED_MODEL_SEARCH", "custom-model")
    reg = EmbeddingProviderRegistry(SemanticConfig())
    assert reg.get_model_name("search") == "custom-model"
