from __future__ import annotations

from fala_gavea.domain.entities.vote import VoteSummary
from fala_gavea.domain.repositories.vote_repository import IVoteRepository


class GetVoteSummaryUseCase:
    def __init__(self, vote_repo: IVoteRepository) -> None:
        self._vote_repo = vote_repo

    def execute(
        self,
        target_type: str,
        target_id: str,
        voter_id: str | None = None,
    ) -> VoteSummary:
        return self._vote_repo.get_summary(target_type, target_id, voter_id)
