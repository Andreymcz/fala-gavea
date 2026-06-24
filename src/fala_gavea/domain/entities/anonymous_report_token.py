from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnonymousReportToken:
    id: str
    report_id: str
    token_hash: str
    created_at: datetime
