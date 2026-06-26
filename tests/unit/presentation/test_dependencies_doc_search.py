from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import fala_gavea.presentation.api.dependencies as deps


@pytest.fixture(autouse=True)
def _reset_module_globals():
    """get_embedding_model / get_doc_search_port use module-global singletons.

    Tests must reset them before and after each run so state never leaks across
    tests (a stale cached model/port or a sticky _DOC_INIT_FAILED sentinel would
    make other tests pass/fail spuriously).
    """
    deps._embedding_model_instance = None
    deps._doc_search_instance = None
    yield
    deps._embedding_model_instance = None
    deps._doc_search_instance = None


def test_get_embedding_model_is_cached_singleton() -> None:
    fake_model = object()
    with patch(
        "sentence_transformers.SentenceTransformer", return_value=fake_model
    ) as ctor:
        first = deps.get_embedding_model()
        second = deps.get_embedding_model()
    assert first is fake_model
    assert second is fake_model
    # loaded exactly once despite two calls
    ctor.assert_called_once()


def test_get_doc_search_port_builds_with_shared_model() -> None:
    fake_model = object()
    fake_port = object()
    with (
        patch.object(deps, "get_embedding_model", return_value=fake_model) as get_model,
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_doc_search_client.ChromaDocSearchClient",
            return_value=fake_port,
        ) as ctor,
    ):
        port = deps.get_doc_search_port()
    assert port is fake_port
    get_model.assert_called_once()
    # model is injected into the client (shared instance preserved)
    _, kwargs = ctor.call_args
    args = ctor.call_args.args
    assert fake_model in args or fake_model in kwargs.values()


def test_get_doc_search_port_returns_none_on_failure() -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("chroma down")

    with (
        patch.object(deps, "get_embedding_model", return_value=object()),
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_doc_search_client.ChromaDocSearchClient",
            side_effect=_boom,
        ),
    ):
        assert deps.get_doc_search_port() is None
        # subsequent call still returns None (failure is sticky, no re-attempt)
        assert deps.get_doc_search_port() is None


def test_chroma_search_client_backward_compat_no_model_arg() -> None:
    """ChromaSearchClient(config) without a model still constructs (scripts/tests)."""
    from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
    from fala_gavea.infrastructure.embeddings.registry import SemanticConfig

    with (
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_search_client.chromadb.PersistentClient"
        ),
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_search_client.SentenceTransformer"
        ) as mock_st,
    ):
        mock_st.return_value = MagicMock()
        client = ChromaSearchClient(SemanticConfig(vectorstore_path="/tmp/test-vs"))
    assert client is not None
    # constructed its own model since none was injected
    mock_st.assert_called_once()


def test_chroma_search_client_uses_injected_model() -> None:
    from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
    from fala_gavea.infrastructure.embeddings.registry import SemanticConfig

    injected = MagicMock()
    with (
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_search_client.chromadb.PersistentClient"
        ),
        patch(
            "fala_gavea.infrastructure.chromadb.chroma_search_client.SentenceTransformer"
        ) as mock_st,
    ):
        client = ChromaSearchClient(
            SemanticConfig(vectorstore_path="/tmp/test-vs"), model=injected
        )
    # injected model used; no SentenceTransformer constructed
    assert client._model is injected
    mock_st.assert_not_called()
