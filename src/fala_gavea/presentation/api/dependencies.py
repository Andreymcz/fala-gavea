from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from ...infrastructure.database.session import SessionLocal
from ...infrastructure.repositories.sqlalchemy_report_repository import (
    SQLAlchemyReportRepository,
)


def get_report_repo() -> Generator[SQLAlchemyReportRepository, None, None]:
    db: Session = SessionLocal()
    try:
        yield SQLAlchemyReportRepository(db)
    finally:
        db.close()
