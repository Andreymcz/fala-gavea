from __future__ import annotations

from abc import ABC, abstractmethod

from fala_gavea.domain.entities.vote import Vote, VoteSummary


class IVoteRepository(ABC):
    @abstractmethod
    def cast(self, vote: Vote) -> Vote: ...

    @abstractmethod
    def retract(self, voter_id: str, target_type: str, target_id: str) -> None: ...

    @abstractmethod
    def get_summary(
        self, target_type: str, target_id: str, voter_id: str | None
    ) -> VoteSummary: ...

    @abstractmethod
    def get_summaries_batch(
        self, target_type: str, target_ids: list[str], voter_id: str | None = None
    ) -> dict[str, VoteSummary]: ...
