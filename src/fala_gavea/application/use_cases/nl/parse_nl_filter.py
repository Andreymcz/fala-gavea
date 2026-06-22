from __future__ import annotations
from dataclasses import dataclass, field
from fala_gavea.domain.repositories.filter_ports import IFilterParser, ParseError  # noqa: F401

_ALLOWED_KEYS = {
    "report_type_ids", "urgencies", "statuses",
    "since", "until", "text", "q",
}


@dataclass
class ParseNLFilterResult:
    body: dict
    warnings: list[str] = field(default_factory=list)


class ParseNLFilter:
    def __init__(self, filter_parser: IFilterParser | None) -> None:
        self._parser = filter_parser

    def execute(self, text: str) -> ParseNLFilterResult:
        if self._parser is None:
            raise RuntimeError("filter_parser not configured")
        raw = self._parser.parse(text)
        filtered = {k: v for k, v in raw.items() if k in _ALLOWED_KEYS and v is not None}
        warnings: list[str] = []
        unknown = set(raw.keys()) - _ALLOWED_KEYS
        if unknown:
            warnings.append(f"Campos ignorados: {sorted(unknown)}")
        return ParseNLFilterResult(body=filtered, warnings=warnings)
