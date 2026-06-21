from dataclasses import dataclass
from datetime import datetime


@dataclass
class SavedFilter:
    id: str          # UUID4
    owner_id: str    # FK → users.id
    name: str        # 1–80 chars
    body: str        # JSON string: ReportQueryBody subset
    schema_ver: str  # defaults to "1"
    created_at: datetime
    updated_at: datetime
