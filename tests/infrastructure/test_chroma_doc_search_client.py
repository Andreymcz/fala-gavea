from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from fala_gavea.domain.repositories.doc_ports import DocChunk
from fala_gavea.infrastructure.chromadb.chroma_doc_search_client import (
    ChromaDocSearchClient,
)


@dataclass
class _StubConfig:
    """Minimal stand-in for SemanticConfig with the fields the client reads."""

    vectorstore_path: str
    selfdocs_collection: str = "test_selfdocs"


class _FakeEncoder:
    """Deterministic, download-free encoder.

    Maps any text to a fixed-length vector by hashing characters into N buckets.
    Ranking quality is irrelevant for these tests — what matters is that index
    and query vectors share the same dimension so Chroma can compute distances,
    and that the server-side `where` filter excludes rows before ranking.
    """

    _DIM = 16

    def _vec(self, text: str) -> list[float]:
        vec = [0.0] * self._DIM
        for i, ch in enumerate(text):
            vec[(ord(ch) + i) % self._DIM] += 1.0
        return vec

    def encode(self, texts, batch_size: int = 32, show_progress_bar: bool = False) -> np.ndarray:
        # Mirror SentenceTransformer: str -> 1D vector, list[str] -> 2D matrix.
        if isinstance(texts, str):
            return np.asarray(self._vec(texts), dtype=np.float32)
        return np.asarray([self._vec(t) for t in texts], dtype=np.float32)


def _chunk(chunk_id: str, text: str, visibility: str) -> DocChunk:
    return DocChunk(
        chunk_id=chunk_id,
        text=text,
        source_path=f"_output/plans/{chunk_id}.md",
        doc_type="plan",
        section_title="Intro",
        chunk_index=0,
        role_visibility=visibility,
    )


@pytest.fixture
def client(tmp_path) -> ChromaDocSearchClient:
    config = _StubConfig(vectorstore_path=str(tmp_path), selfdocs_collection="test_selfdocs")
    return ChromaDocSearchClient(config, _FakeEncoder())


def test_ready_false_on_empty_then_true_after_reindex(client: ChromaDocSearchClient) -> None:
    assert client.ready() is False
    assert client.count() == 0

    client.reindex_all(
        [
            _chunk("pub", "conteudo publico sobre seguranca", "public"),
            _chunk("int", "conteudo interno confidencial", "internal"),
        ]
    )

    assert client.ready() is True


def test_count_matches_number_of_indexed_chunks(client: ChromaDocSearchClient) -> None:
    client.reindex_all(
        [
            _chunk("pub", "conteudo publico", "public"),
            _chunk("int", "conteudo interno", "internal"),
        ]
    )
    assert client.count() == 2


def test_reindex_empty_recreates_and_stays_empty(client: ChromaDocSearchClient) -> None:
    client.reindex_all([_chunk("pub", "algo", "public")])
    assert client.count() == 1

    client.reindex_all([])
    assert client.count() == 0
    assert client.ready() is False


def test_search_public_role_excludes_internal(client: ChromaDocSearchClient) -> None:
    client.reindex_all(
        [
            _chunk("pub", "conteudo publico sobre seguranca", "public"),
            _chunk("int", "conteudo interno confidencial", "internal"),
        ]
    )

    hits = client.search("seguranca", roles=["public"], n=5)

    # Fail-closed: the internal chunk must NEVER surface for a public-only role.
    assert len(hits) == 1
    assert all(hit.chunk.role_visibility != "internal" for hit in hits)
    assert hits[0].chunk.chunk_id == "pub"
    assert hits[0].chunk.role_visibility == "public"


def test_search_returns_doc_search_hit_with_full_chunk(client: ChromaDocSearchClient) -> None:
    client.reindex_all([_chunk("pub", "conteudo publico", "public")])

    hits = client.search("conteudo", roles=["public"], n=5)

    assert len(hits) == 1
    hit = hits[0]
    assert hit.chunk.chunk_id == "pub"
    assert hit.chunk.text == "conteudo publico"
    assert hit.chunk.source_path == "_output/plans/pub.md"
    assert hit.chunk.doc_type == "plan"
    assert hit.chunk.section_title == "Intro"
    assert hit.chunk.chunk_index == 0
    assert isinstance(hit.chunk.chunk_index, int)
    assert 0.0 <= hit.score <= 1.0


def test_search_both_roles_can_return_both(client: ChromaDocSearchClient) -> None:
    client.reindex_all(
        [
            _chunk("pub", "conteudo publico sobre seguranca", "public"),
            _chunk("int", "conteudo interno sobre seguranca", "internal"),
        ]
    )

    hits = client.search("seguranca", roles=["public", "internal"], n=5)

    returned_ids = {hit.chunk.chunk_id for hit in hits}
    assert returned_ids == {"pub", "int"}


def test_search_on_empty_collection_returns_empty(client: ChromaDocSearchClient) -> None:
    assert client.search("qualquer", roles=["public"], n=5) == []
