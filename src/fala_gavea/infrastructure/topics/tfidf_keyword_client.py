from __future__ import annotations

import logging
from collections import Counter

from fala_gavea.domain.entities.report import Report
from fala_gavea.domain.repositories.semantic_ports import ITopicModelPort

logger = logging.getLogger(__name__)

_DEFAULT_N_CLUSTERS = 8
_DEFAULT_MAX_TERMS = 8


class TfidfKeywordClient(ITopicModelPort):
    """Keyword extraction via TF-IDF + K-means. No embedding model required."""

    def __init__(self, n_clusters: int = _DEFAULT_N_CLUSTERS, max_terms: int = _DEFAULT_MAX_TERMS) -> None:
        self._n_clusters = n_clusters
        self._max_terms = max_terms

    def infer_topics(self, reports: list[Report]) -> list[dict]:
        from sklearn.cluster import KMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        texts = [r.text for r in reports]
        if len(texts) < 2:
            return []

        n_clusters = min(self._n_clusters, len(texts))

        try:
            vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=1,
                sublinear_tf=True,
            )
            X = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)

            counts: Counter[int] = Counter(labels.tolist())
            centers = kmeans.cluster_centers_

            result: list[dict] = []
            for topic_id, count in counts.most_common():
                top_indices = np.argsort(centers[topic_id])[::-1][: self._max_terms]
                terms = [str(feature_names[i]) for i in top_indices]
                result.append({"topic_id": int(topic_id), "terms": terms, "count": int(count)})

            return result

        except Exception as exc:
            logger.error("TF-IDF topic extraction failed: %s", exc)
            return []

    def fit(self, reports: list[Report]) -> None:
        raise NotImplementedError("TfidfKeywordClient does not support pre-fitting.")

    def topic_of(self, report: Report) -> int:
        raise NotImplementedError("TfidfKeywordClient does not support per-document topic lookup.")

    def list_topics(self) -> list[dict]:
        raise NotImplementedError("TfidfKeywordClient does not maintain a persistent topic list.")
