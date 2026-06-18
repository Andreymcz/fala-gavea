from __future__ import annotations

from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.repositories.forwarding_repository import (
    ForwardingFilters,
    IForwardingRepository,
)


class ListForwardings:
    def __init__(self, forwarding_repo: IForwardingRepository) -> None:
        self._forwarding_repo = forwarding_repo

    def execute(self, filters: ForwardingFilters) -> list[Forwarding]:
        return self._forwarding_repo.find_all(filters)
