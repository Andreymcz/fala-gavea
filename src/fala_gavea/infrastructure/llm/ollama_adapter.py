from __future__ import annotations
from fala_gavea.domain.repositories.semantic_ports import ILLMClient
from fala_gavea.infrastructure.ollama.ollama_client import OllamaClient


class OllamaAdapter(ILLMClient):
    def __init__(self) -> None:
        self._client = OllamaClient()

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        return self._client.chat(full_messages)
