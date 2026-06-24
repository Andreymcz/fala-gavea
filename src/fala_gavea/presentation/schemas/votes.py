from __future__ import annotations

from pydantic import BaseModel


class VoteSummarySchema(BaseModel):
    upvotes: int
    downvotes: int
    user_vote: int | None


class CastVoteRequest(BaseModel):
    value: int
