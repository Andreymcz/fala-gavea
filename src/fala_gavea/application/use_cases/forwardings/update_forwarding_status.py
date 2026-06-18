from __future__ import annotations

from datetime import datetime, timezone

from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository


class UpdateForwardingStatus:
    def __init__(self, forwarding_repo: IForwardingRepository) -> None:
        self._forwarding_repo = forwarding_repo

    def execute(self, id: str, status_str: str) -> Forwarding:
        try:
            new_status = ForwardingStatus(status_str)
        except ValueError:
            raise InvalidInputError(
                "status must be one of: aguardando_solucao, solucao_em_andamento, finalizado"
            )

        forwarding = self._forwarding_repo.find_by_id(id)
        if forwarding is None:
            raise ForwardingNotFoundError(id)

        forwarding.status = new_status
        forwarding.updated_at = datetime.now(timezone.utc)
        return self._forwarding_repo.save(forwarding)
