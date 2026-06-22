from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus


@dataclass
class ForwardingFilters:
    status: ForwardingStatus | None = None
    institution: str | None = None  # substring match
    agent_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None


class IForwardingRepository(ABC):
    @abstractmethod
    def save(self, forwarding: Forwarding) -> Forwarding: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Forwarding | None: ...

    @abstractmethod
    def find_all(self, filters: ForwardingFilters) -> list[Forwarding]: ...

    @abstractmethod
    def add_reports(self, forwarding_id: str, report_ids: list[str]) -> None:
        """Link reports to a forwarding (inserts ForwardingReport rows)."""

    @abstractmethod
    def get_report_ids(self, forwarding_id: str) -> list[str]: ...

    @abstractmethod
    def find_by_report_id(self, report_id: str) -> list[Forwarding]:
        """Return all forwardings linked to the given report (reverse of add_reports)."""
