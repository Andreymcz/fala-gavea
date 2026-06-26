from __future__ import annotations

import pytest

from fala_gavea.domain.repositories.doc_ports import (
    DocChunk,
    DocSearchHit,
    IDocIndexer,
    IDocSearchPort,
)


def _sample_chunk() -> DocChunk:
    return DocChunk(
        chunk_id="_output/plans/plan-000174.md#0",
        text="some chunk text",
        source_path="_output/plans/plan-000174.md",
        doc_type="plan",
        section_title="## Overview",
        chunk_index=0,
        role_visibility="public",
    )


def test_doc_chunk_field_types() -> None:
    chunk = _sample_chunk()
    assert chunk.chunk_id == "_output/plans/plan-000174.md#0"
    assert chunk.text == "some chunk text"
    assert chunk.source_path == "_output/plans/plan-000174.md"
    assert chunk.doc_type == "plan"
    assert chunk.section_title == "## Overview"
    assert chunk.chunk_index == 0
    assert chunk.role_visibility == "public"


def test_doc_chunk_section_title_can_be_empty() -> None:
    chunk = DocChunk(
        chunk_id="readme.md#1",
        text="t",
        source_path="readme.md",
        doc_type="readme",
        section_title="",
        chunk_index=1,
        role_visibility="internal",
    )
    assert chunk.section_title == ""


def test_doc_search_hit_field_types() -> None:
    chunk = _sample_chunk()
    hit = DocSearchHit(chunk=chunk, score=0.87)
    assert hit.chunk is chunk
    assert hit.score == 0.87


def test_doc_search_port_is_abstract() -> None:
    with pytest.raises(TypeError):
        IDocSearchPort()  # type: ignore[abstract]


def test_doc_indexer_is_abstract() -> None:
    with pytest.raises(TypeError):
        IDocIndexer()  # type: ignore[abstract]
