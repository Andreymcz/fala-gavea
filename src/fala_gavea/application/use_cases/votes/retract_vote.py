from __future__ import annotations

from fala_gavea.domain.repositories.vote_repository import IVoteRepository


class RetractVoteUseCase:
    def __init__(self, vote_repo: IVoteRepository) -> None:
        self._vote_repo = vote_repo

    def execute(self, voter_id: str, target_type: str, target_id: str) -> None:
        self._vote_repo.retract(voter_id, target_type, target_id)
