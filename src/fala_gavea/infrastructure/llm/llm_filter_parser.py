from __future__ import annotations
import json
import logging
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError
from fala_gavea.domain.repositories.semantic_ports import ILLMClient

_log = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um assistente que converte texto em português para um filtro estruturado JSON.
Retorne SOMENTE um objeto JSON válido com zero ou mais dos campos abaixo (omita campos não mencionados):
{
  "report_type_ids": [],   // lista de strings (IDs de tipo)
  "urgencies": [],         // lista de: "alta", "media", "baixa"
  "statuses": [],          // lista de: "pendente", "em_analise", "encaminhado", "resolvido"
  "since": null,           // ISO 8601 date string ou null
  "until": null,           // ISO 8601 date string ou null
  "text": null,            // string de busca textual ou null
  "q": null                // string de busca semântica ou null
}
Não inclua explicações. Retorne apenas JSON."""


class LLMFilterParser(IFilterParser):
    def __init__(self, llm_client: ILLMClient) -> None:
        self._llm = llm_client

    def parse(self, text: str) -> dict:
        _log.debug("LLMFilterParser.parse input=%r", text)
        raw = self._llm.complete_with_timeout(_SYSTEM_PROMPT, [{"role": "user", "content": text}], timeout_s=30.0)
        _log.debug("LLMFilterParser raw response=%r", raw)
        result, warnings = self._try_parse(raw)
        if result is not None:
            _log.debug("LLMFilterParser parsed OK: %s", result)
            return result
        _log.warning("LLMFilterParser attempt 1 failed to parse, retrying. raw=%r", raw)
        # one repair retry
        repair_prompt = (
            f"O JSON anterior estava malformado: {raw!r}\n"
            "Retorne apenas o JSON válido, sem nenhum texto extra."
        )
        raw2 = self._llm.complete_with_timeout(_SYSTEM_PROMPT, [
            {"role": "user", "content": text},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": repair_prompt},
        ], timeout_s=30.0)
        _log.debug("LLMFilterParser retry response=%r", raw2)
        result2, _ = self._try_parse(raw2)
        if result2 is not None:
            _log.debug("LLMFilterParser parsed OK on retry: %s", result2)
            return result2
        _log.error("LLMFilterParser failed after retry. raw1=%r raw2=%r", raw, raw2)
        raise ParseError(message="LLM returned invalid JSON after retry", raw=raw2)

    @staticmethod
    def _try_parse(raw: str) -> tuple[dict | None, list[str]]:
        try:
            data = json.loads(raw.strip())
            if isinstance(data, dict):
                return data, []
        except json.JSONDecodeError:
            pass
        import re
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                if isinstance(data, dict):
                    return data, ["extracted from markdown block"]
            except json.JSONDecodeError:
                pass
        return None, []
