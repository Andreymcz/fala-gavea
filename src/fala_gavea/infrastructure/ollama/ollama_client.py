from __future__ import annotations

import os
from typing import Any

import httpx

from fala_gavea.domain.exceptions import OllamaUnavailableError

_DEFAULT_MODEL = "qwen3:8b"


class OllamaClient:
    """HTTP client for Ollama's /api/chat endpoint.

    Gracefully degrades when FALA_GAVEA_OLLAMA_URL is not set:
    any method call raises OllamaUnavailableError (→ HTTP 503 at the router level).
    """

    def __init__(self) -> None:
        url = os.environ.get("FALA_GAVEA_OLLAMA_URL", "").strip()
        if not url:
            self._available = False
            self._base_url = ""
        else:
            self._available = True
            self._base_url = url.rstrip("/")
        self._model = os.environ.get("FALA_GAVEA_OLLAMA_MODEL", _DEFAULT_MODEL)

    def _require_available(self) -> None:
        if not self._available:
            raise OllamaUnavailableError()

    def chat(self, messages: list[dict[str, Any]], stream: bool = False, timeout: float = 120.0) -> str:
        """Send a chat request to Ollama and return the assistant reply as a string."""
        self._require_available()
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
        }
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
