from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParseError(Exception):
    message: str
    partial: dict = field(default_factory=dict)
    raw: str = ""


class IFilterParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> dict:
        """Parse natural language into a ReportQueryRequest-compatible dict.

        Raises ParseError on unrecoverable failure.
        """
