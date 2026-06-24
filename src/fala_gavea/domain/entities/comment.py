from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Comment:
    id: str
    forwarding_id: str
    author_id: str
    text: str
    created_at: datetime
