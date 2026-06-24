from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.vote import Vote, VoteSummary
from fala_gavea.domain.repositories.vote_repository import IVoteRepository
from fala_gavea.infrastructure.database.models import VoteModel


def _find_vote(session: Session, voter_id: str, target_type: str, target_id: str) -> VoteModel | None:
    return session.execute(
        select(VoteModel).where(
            VoteModel.voter_id == voter_id,
            VoteModel.target_type == target_type,
            VoteModel.target_id == target_id,
        )
    ).scalar_one_or_none()


class SQLAlchemyVoteRepository(IVoteRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def cast(self, vote: Vote) -> Vote:
        model = _find_vote(self._session, vote.voter_id, vote.target_type, vote.target_id)
        if model is None:
            model = VoteModel(
                id=vote.id,
                voter_id=vote.voter_id,
                target_type=vote.target_type,
                target_id=vote.target_id,
                value=vote.value,
                created_at=vote.created_at,
            )
            self._session.add(model)
        else:
            model.value = vote.value
        self._session.commit()
        return vote

    def retract(self, voter_id: str, target_type: str, target_id: str) -> None:
        model = _find_vote(self._session, voter_id, target_type, target_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()

    def get_summary(
        self,
        target_type: str,
        target_id: str,
        voter_id: str | None = None,
    ) -> VoteSummary:
        stmt = select(func.count()).where(
            VoteModel.target_type == target_type,
            VoteModel.target_id == target_id,
            VoteModel.value == 1,
        )
        upvotes: int = self._session.scalar(stmt) or 0

        stmt2 = select(func.count()).where(
            VoteModel.target_type == target_type,
            VoteModel.target_id == target_id,
            VoteModel.value == -1,
        )
        downvotes: int = self._session.scalar(stmt2) or 0

        user_vote: int | None = None
        if voter_id is not None:
            model = _find_vote(self._session, voter_id, target_type, target_id)
            if model is not None:
                user_vote = model.value

        return VoteSummary(upvotes=upvotes, downvotes=downvotes, user_vote=user_vote)
