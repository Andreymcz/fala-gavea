from __future__ import annotations

import os

import chromadb
from sentence_transformers import SentenceTransformer

from fala_gavea.domain.repositories.doc_ports import DocChunk, DocSearchHit, IDocIndexer, IDocSearchPort
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig

_DEFAULT_COLLECTION_NAME = "falagavea_selfdocs"


class ChromaDocSearchClient(IDocIndexer, IDocSearchPort):
    """Role-filtered semantic search over the project's own documentation.

    Uses a separate Chroma collection from the reports search client and accepts a
    pre-loaded SentenceTransformer (injected, so a single model instance can be shared).
    """

    def __init__(self, config: SemanticConfig, model: SentenceTransformer) -> None:
        os.makedirs(config.vectorstore_path, exist_ok=True)
        # selfdocs_collection is added to SemanticConfig in a later step; read defensively
        # so this client stays independently testable and forward-compatible.
        self._collection_name: str = getattr(
            config, "selfdocs_collection", _DEFAULT_COLLECTION_NAME
        )
        self._client = chromadb.PersistentClient(path=config.vectorstore_path)
        self._model = model
        self._collection = self._client.get_or_create_collection(self._collection_name)

    # ------------------------------------------------------------------
    # IDocIndexer
    # ------------------------------------------------------------------

    def reindex_all(self, chunks: list[DocChunk], *, show_progress: bool = False) -> None:
        self._client.delete_collection(self._collection_name)
        self._collection = self._client.get_or_create_collection(self._collection_name)
        if not chunks:
            return
        embeddings = self._model.encode(
            [f"passage: {c.text}" for c in chunks],
            batch_size=64,
            show_progress_bar=show_progress,
        ).tolist()
        self._collection.add(
            ids=[c.chunk_id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source_path": c.source_path,
                    "doc_type": c.doc_type,
                    "section_title": c.section_title,
                    "chunk_index": int(c.chunk_index),  # Chroma rejects numpy/str ints here
                    "role_visibility": c.role_visibility,
                }
                for c in chunks
            ],
        )

    def count(self) -> int:
        return self._collection.count()

    # ------------------------------------------------------------------
    # IDocSearchPort
    # ------------------------------------------------------------------

    def search(self, query: str, *, roles: list[str], n: int = 5) -> list[DocSearchHit]:
        if self._collection.count() == 0:
            return []
        embedding = self._model.encode(f"query: {query}").tolist()
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=n,
            # SECURITY: the role filter MUST always be present so Chroma excludes
            # disallowed rows server-side, before ranking. Fail-closed by construction.
            where={"role_visibility": {"$in": roles}},
        )
        ids = result["ids"][0]
        if not ids:
            return []
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        hits: list[DocSearchHit] = []
        for chunk_id, text, meta, dist in zip(ids, documents, metadatas, distances):
            chunk = DocChunk(
                chunk_id=chunk_id,
                text=text,
                source_path=str(meta["source_path"]),
                doc_type=str(meta["doc_type"]),
                section_title=str(meta["section_title"]),
                chunk_index=int(meta["chunk_index"]),
                role_visibility=str(meta["role_visibility"]),
            )
            hits.append(DocSearchHit(chunk=chunk, score=1.0 / (1.0 + dist)))
        return hits

    def ready(self) -> bool:
        return self._collection.count() > 0
