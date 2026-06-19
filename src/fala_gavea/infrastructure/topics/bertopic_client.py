from __future__ import annotations

import logging
from collections import Counter

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.semantic_ports import ITopicModelPort
from fala_gavea.infrastructure.embeddings.registry import SemanticConfig

logger = logging.getLogger(__name__)


class BERTopicClient(ITopicModelPort):
    """On-demand BERTopic inference for a filtered set of reports.

    Only `infer_topics` is implemented; the batch-mode methods (`fit`,
    `topic_of`, `list_topics`) are reserved for a future iteration.
    """

    def __init__(self, config: SemanticConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # ITopicModelPort — primary method
    # ------------------------------------------------------------------

    def infer_topics(self, reports: list[Report]) -> list[dict]:  # noqa: D102
        """Run BERTopic on *reports* and return per-topic summaries.

        Returns a list of dicts ``{topic_id, terms, count}`` sorted by
        descending count.  Topic ``-1`` (BERTopic outlier bucket) is
        excluded.  Returns ``[]`` on any error.
        """
        # bertopic import is intentionally scoped to this module (CONVENTION_1)
        try:
            from bertopic import BERTopic  # type: ignore[import-untyped]
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            logger.error("bertopic/sentence-transformers not available: %s", exc)
            return []

        texts = [r.text for r in reports]
        if not texts:
            return []

        try:
            embedding_model = SentenceTransformer(self._config.embed_model_topics)
            topic_model = BERTopic(
                embedding_model=embedding_model,
                min_topic_size=2,
                verbose=False,
            )
            topics, _ = topic_model.fit_transform(texts)

            # Build topic -> count map (exclude outlier topic -1)
            counts: Counter[int] = Counter(t for t in topics if t != -1)

            result: list[dict] = []
            for topic_id, count in counts.most_common():
                topic_info = topic_model.get_topic(topic_id)
                if not topic_info or not isinstance(topic_info, list):
                    continue
                terms = [str(term) for term, _ in topic_info]
                result.append({"topic_id": topic_id, "terms": terms, "count": count})

            return result

        except Exception as exc:  # noqa: BLE001
            logger.error("BERTopic inference failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # ITopicModelPort — stub methods (batch mode, future iteration)
    # ------------------------------------------------------------------

    def fit(self, reports: list[Report]) -> None:  # noqa: D102
        raise NotImplementedError(
            "BERTopicClient.fit() is reserved for batch mode (future iteration). "
            "Use infer_topics() for on-demand inference."
        )

    def topic_of(self, report: Report) -> int:  # noqa: D102
        raise NotImplementedError(
            "BERTopicClient.topic_of() requires a pre-fitted model (future iteration). "
            "Use infer_topics() for on-demand inference."
        )

    def list_topics(self) -> list[dict]:  # noqa: D102
        raise NotImplementedError(
            "BERTopicClient.list_topics() requires a pre-fitted model (future iteration). "
            "Use infer_topics() for on-demand inference."
        )
