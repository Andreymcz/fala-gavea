from __future__ import annotations

from datetime import datetime, timezone

from fala_gavea.domain.entities.forwarding import Forwarding
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository


class UpdateForwarding:
    def __init__(self, forwarding_repo: IForwardingRepository) -> None:
        self._forwarding_repo = forwarding_repo

    def execute(
        self,
        id: str,
        institution: str | None,
        proposed_solution: str | None,
    ) -> Forwarding:
        forwarding = self._forwarding_repo.find_by_id(id)
        if forwarding is None:
            raise ForwardingNotFoundError(id)

        if institution is not None:
            institution = institution.strip()
            if not (3 <= len(institution) <= 200):
                raise InvalidInputError("institution must be 3-200 characters")
            forwarding.institution = institution

        if proposed_solution is not None:
            proposed_solution = proposed_solution.strip()
            if not (20 <= len(proposed_solution) <= 5000):
                raise InvalidInputError("proposed_solution must be 20-5000 characters")
            forwarding.proposed_solution = proposed_solution

        forwarding.updated_at = datetime.now(timezone.utc)
        return self._forwarding_repo.save(forwarding)
