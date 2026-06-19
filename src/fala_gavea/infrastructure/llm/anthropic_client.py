from __future__ import annotations

import os
from anthropic import Anthropic
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AnthropicClient(ILLMClient):
    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set")
        self._client = Anthropic(api_key=api_key)
        self._model = os.environ.get("FALA_GAVEA_ANTHROPIC_MODEL", _DEFAULT_MODEL)

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
