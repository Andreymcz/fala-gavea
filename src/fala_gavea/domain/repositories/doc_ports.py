from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DocChunk:
    chunk_id: str  # f"{source_path}#{chunk_index}"
    text: str
    source_path: str  # repo-relative, e.g. "_output/plans/plan-000174-...md"
    doc_type: str  # plan | research | reflection | communication | design | journey | constitution | readme | other
    section_title: str  # nearest markdown heading, "" if none
    chunk_index: int
    role_visibility: str  # "public" | "internal"


@dataclass
class DocSearchHit:
    chunk: DocChunk
    score: float  # [0,1]


class IDocSearchPort(ABC):
    @abstractmethod
    def search(self, query: str, *, roles: list[str], n: int = 5) -> list[DocSearchHit]:
        """Top-n chunks whose role_visibility is allowed for `roles`. [] when empty/unavailable."""
        ...

    @abstractmethod
    def ready(self) -> bool:
        """True if the collection is initialized and queryable."""
        ...


class IDocIndexer(ABC):
    @abstractmethod
    def reindex_all(self, chunks: list[DocChunk]) -> None:
        """Replace the entire self-docs collection with the given chunks."""
        ...

    @abstractmethod
    def count(self) -> int: ...
