from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class SemanticConfig:
    embed_model_search: str = field(
        default_factory=lambda: os.getenv(
            "FALA_GAVEA_EMBED_MODEL_SEARCH", "intfloat/multilingual-e5-base"
        )
    )
    embed_model_topics: str = field(
        default_factory=lambda: os.getenv(
            "FALA_GAVEA_EMBED_MODEL_TOPICS", "paraphrase-multilingual-MiniLM-L12-v2"
        )
    )
    vectorstore_path: str = field(
        default_factory=lambda: os.getenv("FALA_GAVEA_VECTORSTORE_PATH", "vectorstore")
    )


class EmbeddingProviderRegistry:
    def __init__(self, config: SemanticConfig) -> None:
        self._map: dict[str, str] = {
            "search": config.embed_model_search,
            "rag": config.embed_model_search,
            "topics": config.embed_model_topics,
        }

    def get_model_name(self, purpose: str) -> str:
        if purpose not in self._map:
            raise ValueError(f"Unknown embedding purpose: {purpose!r}")
        return self._map[purpose]
