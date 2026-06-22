from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.infrastructure.chromadb.chroma_search_client import ChromaSearchClient
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig


def _make_report(rid: str = "r1") -> Report:
    return Report(
        id=rid,
        text="buraco na rua principal",
        lat=-22.97,
        lon=-43.21,
        urgency=Urgency.alta,
        photo_url=None,
        report_type_id="tipo-1",
        author_id="user-1",
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )


@pytest.fixture()
def mocked_client():
    fake_embedding = [0.1, 0.2, 0.3]

    with (
        patch("fala_gavea.infrastructure.chromadb.chroma_search_client.chromadb.PersistentClient") as mock_chroma,
        patch("fala_gavea.infrastructure.chromadb.chroma_search_client.SentenceTransformer") as mock_st,
    ):
        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: fake_embedding)
        mock_st.return_value = mock_model

        mock_collection = MagicMock()
        mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

        config = SemanticConfig(vectorstore_path="/tmp/test-vectorstore")
        client = ChromaSearchClient(config)
        yield client, mock_collection, mock_model


def test_index_calls_collection_add(mocked_client) -> None:
    client, collection, _ = mocked_client
    report = _make_report("r1")
    client.index(report)
    collection.add.assert_called_once()
    call_kwargs = collection.add.call_args.kwargs
    assert call_kwargs["ids"] == ["r1"]


def test_search_returns_list_of_tuples(mocked_client) -> None:
    client, collection, _ = mocked_client
    collection.query.return_value = {
        "ids": [["id1"]],
        "distances": [[0.5]],
    }
    results = client.search("buraco")
    assert len(results) == 1
    rid, score = results[0]
    assert rid == "id1"
    assert abs(score - 1.0 / 1.5) < 1e-6


def test_similar_excludes_self(mocked_client) -> None:
    client, collection, _ = mocked_client
    collection.get.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    collection.query.return_value = {
        "ids": [["r1", "r2", "r3"]],
        "distances": [[0.0, 0.4, 0.8]],
    }
    results = client.similar("r1", n=5)
    ids = [r[0] for r in results]
    assert "r1" not in ids
    assert "r2" in ids
    assert "r3" in ids


def test_similar_to_set_centroid_drops_seeds(mocked_client) -> None:
    client, collection, _ = mocked_client
    # two seeds with embeddings -> centroid queried; results drop seeds
    collection.get.return_value = {"embeddings": [[0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]}
    collection.query.return_value = {
        "ids": [["s1", "s2", "n1", "n2"]],
        "distances": [[0.0, 0.1, 0.4, 0.8]],
    }
    results = client.similar_to_set(["s1", "s2"], n=5)
    ids = [r[0] for r in results]
    assert "s1" not in ids
    assert "s2" not in ids
    assert ids == ["n1", "n2"]
    # centroid = mean of the two embeddings
    call_kwargs = collection.query.call_args.kwargs
    assert call_kwargs["query_embeddings"] == [[0.5, 0.5, 1.0]]


def test_similar_to_set_empty_ids_returns_empty(mocked_client) -> None:
    client, _, _ = mocked_client
    assert client.similar_to_set([], n=5) == []


def test_similar_to_set_no_embeddings_returns_empty(mocked_client) -> None:
    client, collection, _ = mocked_client
    collection.get.return_value = {"embeddings": None}
    assert client.similar_to_set(["x"], n=5) == []
