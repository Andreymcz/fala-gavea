from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fala_gavea.domain.entities.vote import Vote
from fala_gavea.domain.exceptions import InvalidInputError, SelfVoteError
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.vote_repository import IVoteRepository

_VALID_TARGET_TYPES = ("report", "forwarding")
_VALID_VALUES = (1, -1)


class CastVoteUseCase:
    def __init__(
        self,
        vote_repo: IVoteRepository,
        report_repo: IReportRepository,
        forwarding_repo: IForwardingRepository,
    ) -> None:
        self._vote_repo = vote_repo
        self._report_repo = report_repo
        self._forwarding_repo = forwarding_repo

    def execute(self, voter_id: str, target_type: str, target_id: str, value: int) -> Vote:
        if target_type not in _VALID_TARGET_TYPES:
            raise InvalidInputError(f"target_type must be one of {_VALID_TARGET_TYPES}")
        if value not in _VALID_VALUES:
            raise InvalidInputError("value must be 1 or -1")

        # Resolve target author to prevent self-voting
        if target_type == "report":
            target = self._report_repo.find_by_id(target_id)
            if target is None:
                from fala_gavea.domain.exceptions import ReportNotFoundError
                raise ReportNotFoundError(target_id)
            target_author_id = target.author_id
        else:
            target = self._forwarding_repo.find_by_id(target_id)
            if target is None:
                from fala_gavea.domain.exceptions import ForwardingNotFoundError
                raise ForwardingNotFoundError(target_id)
            target_author_id = target.agent_id

        if voter_id == target_author_id:
            raise SelfVoteError()

        vote = Vote(
            id=str(uuid4()),
            voter_id=voter_id,
            target_type=target_type,
            target_id=target_id,
            value=value,
            created_at=datetime.now(UTC),
        )
        return self._vote_repo.cast(vote)
