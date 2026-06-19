from __future__ import annotations

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.semantic_ports import ITopicModelPort

_DEFAULT_MIN_DOCS = 3


class GetTopicsForReports:
    """Return BERTopic topic summaries for a pre-filtered list of reports.

    The caller is responsible for filtering reports (e.g. by date range,
    neighbourhood, urgency).  This use case validates the minimum corpus
    size and delegates to the topic model port.
    """

    def __init__(
        self,
        topic_port: ITopicModelPort,
        min_docs: int = _DEFAULT_MIN_DOCS,
    ) -> None:
        self._topic_port = topic_port
        self._min_docs = min_docs

    def execute(self, reports: list[Report]) -> list[dict]:
        """Run topic inference and return a list of topic dicts.

        Each dict: ``{topic_id: int, terms: list[str], count: int}``.
        Returns ``[]`` when the corpus is too small.
        """
        if len(reports) < self._min_docs:
            return []
        return self._topic_port.infer_topics(reports)
