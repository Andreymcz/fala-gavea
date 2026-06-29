from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class ParseError(Exception):
    message: str
    partial: dict = field(default_factory=dict)
    raw: str = ""


@dataclass
class FilterParseContext:
    """Runtime grounding for the NL filter parser.

    Without this the model invents report-type ids (it has no idea the ids are
    UUIDs) and resolves relative dates against its training cutoff instead of
    today. ``report_types`` is a list of ``(id, name)`` pairs the model must
    choose ids from; ``today`` anchors phrases like "últimos 30 dias".
    """

    report_types: list[tuple[str, str]] = field(default_factory=list)
    today: date | None = None


class IFilterParser(ABC):
    @abstractmethod
    def parse(self, text: str, context: FilterParseContext | None = None) -> dict:
        """Parse natural language into a ReportQueryRequest-compatible dict.

        ``context`` supplies the report-type catalog and current date so the
        model returns real ids and correct relative ranges. Raises ParseError
        on unrecoverable failure.
        """
