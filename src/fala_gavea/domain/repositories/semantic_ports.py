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


class ISemanticSearchPort(ABC):
    @abstractmethod
    def search(self, query: str, n: int = 10) -> list[tuple[str, float]]: ...

    @abstractmethod
    def similar(self, report_id: str, n: int = 5) -> list[tuple[str, float]]: ...


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
