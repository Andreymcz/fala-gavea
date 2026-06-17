from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportType:
    id: str
    name: str
    description: str | None
    active: bool
    created_at: datetime
