from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.anonymous_report_token import AnonymousReportToken


class IAnonymousTokenRepository(ABC):
    @abstractmethod
    def save(self, token: AnonymousReportToken) -> AnonymousReportToken: ...

    @abstractmethod
    def find_report_ids_by_hash(self, token_hash: str) -> list[str]: ...
