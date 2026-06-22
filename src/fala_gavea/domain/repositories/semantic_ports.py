from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.report import Report


class IReportIndexer(ABC):
    @abstractmethod
    def index(self, report: Report) -> None: ...

    @abstractmethod
    def delete(self, report_id: str) -> None: ...

    @abstractmethod
    def reindex_all(self, reports: list[Report]) -> None: ...

    @abstractmethod
    def delete_all(self) -> None: ...

    @abstractmethod
    def index_many(self, reports: list[Report], batch_size: int = 64) -> None:
        """Index multiple reports in a single batched operation."""
        for report in reports:
            self.index(report)


class ISemanticSearchPort(ABC):
    @abstractmethod
    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]: ...

    @abstractmethod
    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]: ...

    @abstractmethod
    def similar_to_set(self, report_ids: list[str], n: int = 5) -> list[tuple[str, float]]:
        """Neighbors of the centroid of the given reports' embeddings.

        Averages the embeddings of report_ids into a centroid, queries the index,
        drops any id in report_ids, and returns up to n (id, score) tuples.
        Returns [] when no embeddings are available.
        """
        ...

    @abstractmethod
    def rank(self, query: str, ids: list[str]) -> dict[str, float]: ...
    """Return a similarity score in [0,1] for each id that exists in the index.

    Missing ids are omitted from the result.
    """


class ITopicModelPort(ABC):
    @abstractmethod
    def topic_of(self, report: Report) -> int: ...

    @abstractmethod
    def list_topics(self) -> list[dict]: ...

    @abstractmethod
    def fit(self, reports: list[Report]) -> None: ...

    @abstractmethod
    def infer_topics(self, reports: list[Report]) -> list[dict]:
        """Run BERTopic on the given reports and return topic summaries.

        Each dict has keys: topic_id (int), terms (list[str]), count (int).
        Topic -1 (outliers) is excluded from the result.
        """
        ...


class ILLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, messages: list[dict[str, str]]) -> str: ...

    def complete_with_timeout(
        self, system: str, messages: list[dict[str, str]], timeout_s: float = 120.0
    ) -> str:
        """Default: delegates to complete(). Override for provider-specific timeout support."""
        return self.complete(system, messages)
