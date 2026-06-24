from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VoteSummary:
    upvotes: int
    downvotes: int
    user_vote: int | None  # +1, -1, or None


@dataclass
class Vote:
    id: str
    voter_id: str
    target_type: str  # 'report' | 'forwarding'
    target_id: str
    value: int  # 1 | -1
    created_at: datetime
