from __future__ import annotations

import os
from dataclasses import dataclass, field

# Default self-docs corpus roots. Duplicated from
# infrastructure/docs/markdown_chunker.py to avoid embeddings/->docs/ coupling;
# Rule-of-Three not yet triggered (2 copies). See plan-000177 progress notes.
_DEFAULT_ROOTS = [
    "_output/plans",
    "_output/research-logs",
    "_output/reflections",
    "_output/communication",
    "product-design/project",
]


def _split_roots(s: str) -> list[str]:
    """Split a comma-separated roots string into trimmed, non-empty paths."""
    return [part.strip() for part in s.split(",") if part.strip()]


@dataclass
class SemanticConfig:
    embed_model_search: str = field(
        default_factory=lambda: os.getenv(
            "FALA_GAVEA_EMBED_MODEL_SEARCH", "intfloat/multilingual-e5-small"
        )
    )
    vectorstore_path: str = field(
        default_factory=lambda: os.getenv(
            "CHROMA_DATA_DIR",
            os.getenv("FALA_GAVEA_VECTORSTORE_PATH", "./chroma_data"),
        )
    )
    selfdocs_collection: str = field(
        default_factory=lambda: os.getenv(
            "FALA_GAVEA_SELFDOCS_COLLECTION", "falagavea_selfdocs"
        )
    )
    selfdocs_corpus_roots: list[str] = field(
        default_factory=lambda: _split_roots(os.getenv("FALA_GAVEA_SELFDOCS_ROOTS", ""))
        or _DEFAULT_ROOTS
    )


class EmbeddingProviderRegistry:
    def __init__(self, config: SemanticConfig) -> None:
        self._map: dict[str, str] = {
            "search": config.embed_model_search,
            "rag": config.embed_model_search,
        }

    def get_model_name(self, purpose: str) -> str:
        if purpose not in self._map:
            raise ValueError(f"Unknown embedding purpose: {purpose!r}")
        return self._map[purpose]
