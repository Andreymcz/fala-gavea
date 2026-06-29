from __future__ import annotations
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime
from fala_gavea.domain.repositories.filter_ports import (  # noqa: F401
    FilterParseContext,
    IFilterParser,
    ParseError,
)
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository

_ALLOWED_KEYS = {
    "report_type_ids", "urgencies", "statuses",
    "since", "until", "text", "q",
}


@dataclass
class ParseNLFilterResult:
    body: dict
    warnings: list[str] = field(default_factory=list)


def _normalize(s: str) -> str:
    """Lowercase + strip accents so "Iluminação" matches "iluminacao"."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip().lower()


class ParseNLFilter:
    def __init__(
        self,
        filter_parser: IFilterParser | None,
        report_type_repo: IReportTypeRepository | None = None,
    ) -> None:
        self._parser = filter_parser
        self._report_type_repo = report_type_repo

    def execute(self, text: str) -> ParseNLFilterResult:
        if self._parser is None:
            raise RuntimeError("filter_parser not configured")

        report_types = (
            [(rt.id, rt.name) for rt in self._report_type_repo.find_all_active()]
            if self._report_type_repo is not None
            else []
        )
        context = FilterParseContext(
            report_types=report_types,
            today=datetime.now(UTC).date(),
        )
        raw = self._parser.parse(text, context)
        filtered = {k: v for k, v in raw.items() if k in _ALLOWED_KEYS and v is not None}
        warnings: list[str] = []
        unknown = set(raw.keys()) - _ALLOWED_KEYS
        if unknown:
            warnings.append(f"Campos ignorados: {sorted(unknown)}")

        if "report_type_ids" in filtered and report_types:
            mapped, dropped = self._resolve_report_type_ids(
                filtered["report_type_ids"], report_types
            )
            if mapped:
                filtered["report_type_ids"] = mapped
            else:
                del filtered["report_type_ids"]
            if dropped:
                warnings.append(f"Tipos de relato não reconhecidos: {dropped}")

        return ParseNLFilterResult(body=filtered, warnings=warnings)

    @staticmethod
    def _resolve_report_type_ids(
        values: object, report_types: list[tuple[str, str]]
    ) -> tuple[list[str], list[str]]:
        """Coerce model output into real type IDs.

        The model is told to return catalog IDs, but it still sometimes returns
        a name ("Iluminacao publica") or a bare keyword ("iluminacao"). Resolve
        in tiers: exact ID, exact normalized name, then keyword substring against
        the name. Anything left over is dropped and reported. Order is preserved
        and duplicates removed.
        """
        if not isinstance(values, list):
            values = [values]
        valid_ids = {rt_id for rt_id, _ in report_types}
        by_name = {_normalize(name): rt_id for rt_id, name in report_types}
        norm_names = [(_normalize(name), rt_id) for rt_id, name in report_types]
        resolved: list[str] = []
        dropped: list[str] = []
        for v in values:
            s = str(v)
            norm = _normalize(s)
            if s in valid_ids:
                rt_id = s
            elif norm in by_name:
                rt_id = by_name[norm]
            else:
                # keyword fallback — require >=3 chars to avoid spurious hits
                match = next(
                    (
                        rid
                        for name, rid in norm_names
                        if len(norm) >= 3 and (norm in name or name in norm)
                    ),
                    None,
                )
                if match is None:
                    dropped.append(s)
                    continue
                rt_id = match
            if rt_id not in resolved:
                resolved.append(rt_id)
        return resolved, dropped
