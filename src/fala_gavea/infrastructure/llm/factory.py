from __future__ import annotations

import logging
import os
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_log = logging.getLogger(__name__)


def create_llm_client() -> ILLMClient:
    """Resolve ILLMClient via FALA_GAVEA_LLM_PROVIDER (ollama | anthropic)."""
    provider = os.environ.get("FALA_GAVEA_LLM_PROVIDER", "ollama").strip().lower()
    if provider == "anthropic":
        from fala_gavea.infrastructure.llm.anthropic_client import AnthropicClient
        return AnthropicClient()
    if provider != "ollama":
        _log.warning("Unknown LLM provider %r — falling back to ollama", provider)
    from fala_gavea.infrastructure.llm.ollama_adapter import OllamaAdapter
    return OllamaAdapter()
