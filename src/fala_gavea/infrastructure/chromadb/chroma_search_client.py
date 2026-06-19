from __future__ import annotations

import os

import chromadb
from sentence_transformers import SentenceTransformer

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.semantic_ports import IReportIndexer, ISemanticSearchPort
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig

_COLLECTION_NAME = "falagavea_reports_search"


class ChromaSearchClient(IReportIndexer, ISemanticSearchPort):
    def __init__(self, config: SemanticConfig) -> None:
        os.makedirs(config.vectorstore_path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=config.vectorstore_path)
        self._model = SentenceTransformer(config.embed_model_search)
        self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)

    # ------------------------------------------------------------------
    # Encoding helpers (multilingual-e5 expects prefixes)
    # ------------------------------------------------------------------

    def _encode_passage(self, text: str) -> list[float]:
        return self._model.encode(f"passage: {text}").tolist()

    def _encode_query(self, text: str) -> list[float]:
        return self._model.encode(f"query: {text}").tolist()

    # ------------------------------------------------------------------
    # IReportIndexer
    # ------------------------------------------------------------------

    def index(self, report: Report) -> None:
        embedding = self._encode_passage(report.text)
        self._collection.add(
            ids=[report.id],
            documents=[report.text],
            embeddings=[embedding],
            metadatas=[
                {
                    "lat": report.lat,
                    "lon": report.lon,
                    "urgency": report.urgency.value,
                    "report_type_id": report.report_type_id,
                }
            ],
        )

    def delete(self, report_id: str) -> None:
        self._collection.delete(ids=[report_id])

    def reindex_all(self, reports: list[Report]) -> None:
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(_COLLECTION_NAME)
        if not reports:
            return
        ids = [r.id for r in reports]
        documents = [r.text for r in reports]
        embeddings = [self._encode_passage(r.text) for r in reports]
        metadatas = [
            {
                "lat": r.lat,
                "lon": r.lon,
                "urgency": r.urgency.value,
                "report_type_id": r.report_type_id,
            }
            for r in reports
        ]
        self._collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    # ------------------------------------------------------------------
    # ISemanticSearchPort
    # ------------------------------------------------------------------

    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]:
        embedding = self._encode_query(query)
        result = self._collection.query(query_embeddings=[embedding], n_results=n)
        ids = result["ids"][0]
        distances = result["distances"][0]
        return [(rid, 1.0 / (1.0 + dist)) for rid, dist in zip(ids, distances)]

    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]:
        result = self._collection.get(ids=[report_id], include=["embeddings"])
        embedding = result["embeddings"][0]
        # fetch n+1 to drop the report itself from results
        query_result = self._collection.query(
            query_embeddings=[embedding], n_results=n + 1
        )
        ids = query_result["ids"][0]
        distances = query_result["distances"][0]
        return [
            (rid, 1.0 / (1.0 + dist))
            for rid, dist in zip(ids, distances)
            if rid != report_id
        ][:n]
