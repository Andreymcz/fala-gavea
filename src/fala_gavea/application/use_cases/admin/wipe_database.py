from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from fala_gavea.domain.repositories.semantic_ports import IReportIndexer


@dataclass
class WipeResult:
    reports: int
    forwardings: int
    report_types: int


class WipeDatabase:
    # Raw Session required: bulk DELETE across tables in FK order doesn't fit domain repo ABCs.
    def execute(
        self,
        db: Session,
        include_report_types: bool = False,
        indexer: IReportIndexer | None = None,
    ) -> WipeResult:
        fr_count = db.execute(text("DELETE FROM forwarding_reports")).rowcount
        f_count = db.execute(text("DELETE FROM forwardings")).rowcount
        r_count = db.execute(text("DELETE FROM reports")).rowcount
        rt_count = 0
        if include_report_types:
            rt_count = db.execute(text("DELETE FROM report_types")).rowcount
        db.commit()

        if indexer is not None:
            indexer.delete_all()

        return WipeResult(
            reports=r_count,
            forwardings=f_count + fr_count,
            report_types=rt_count,
        )
