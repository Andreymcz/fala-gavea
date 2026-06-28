from __future__ import annotations

from fala_gavea.domain.repositories.report_repository import IReportRepository, ReportFilters


class ListReportsGeoJSON:
    def __init__(self, report_repo: IReportRepository) -> None:
        self._report_repo = report_repo

    def execute(self, filters: ReportFilters) -> dict:
        reports = self._report_repo.find_all(filters)
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r.lon, r.lat]},
                "properties": {
                    "id": r.id,
                    "text": r.text,
                    "urgency": r.urgency.value,
                    "status": r.status.value,
                    "report_type_id": r.report_type_id,
                    "author_id": r.author_id,
                    "photo_url": r.photo_url,
                    "created_at": r.created_at.isoformat(),
                },
            }
            for r in reports
        ]
        return {"type": "FeatureCollection", "features": features}
