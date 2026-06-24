from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from fala_gavea.domain.entities.report import ReportStatus, Urgency
from fala_gavea.presentation.schemas.votes import VoteSummarySchema


class ReportCreate(BaseModel):
    text: str
    lat: float
    lon: float
    urgency: str
    report_type_id: str
    photo_url: str | None = None

    @field_validator("text")
    @classmethod
    def text_length(cls, v: str) -> str:
        if len(v.strip()) < 10 or len(v) > 2000:
            raise ValueError("text must be 10-2000 characters")
        return v

    @field_validator("lat")
    @classmethod
    def lat_range(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("lat must be between -90 and 90")
        return v

    @field_validator("lon")
    @classmethod
    def lon_range(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("lon must be between -180 and 180")
        return v

    @field_validator("urgency")
    @classmethod
    def urgency_valid(cls, v: str) -> str:
        if v not in {"alta", "media", "baixa"}:
            raise ValueError("urgency must be alta, media, or baixa")
        return v


class ReportResponse(BaseModel):
    id: str
    text: str
    lat: float
    lon: float
    urgency: str
    status: str
    report_type_id: str
    author_id: str
    photo_url: str | None
    created_at: datetime
    votes: VoteSummarySchema | None = None

    model_config = {"from_attributes": True}


class ReportSearchResult(ReportResponse):
    """Hydrated report plus its semantic-similarity score in [0, 1]."""

    score: float


class ReportQueryRequest(BaseModel):
    report_type_ids: list[str] = []
    urgencies: list[str] = []
    statuses: list[str] = []
    since: datetime | None = None
    until: datetime | None = None
    bbox: str | None = None  # "minLat,minLon,maxLat,maxLon"
    text: str | None = None
    author_id: str | None = None
    q: str | None = None
    limit: int = 50
    offset: int = 0

    @field_validator("limit")
    @classmethod
    def limit_range(cls, v: int) -> int:
        if not (1 <= v <= 200):
            raise ValueError("limit must be 1-200")
        return v

    @field_validator("offset")
    @classmethod
    def offset_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset must be >= 0")
        return v

    @field_validator("urgencies")
    @classmethod
    def urgencies_valid(cls, v: list[str]) -> list[str]:
        valid = {e.value for e in Urgency}
        for item in v:
            if item not in valid:
                raise ValueError(f"invalid urgency: {item}")
        return v

    @field_validator("statuses")
    @classmethod
    def statuses_valid(cls, v: list[str]) -> list[str]:
        valid = {e.value for e in ReportStatus}
        for item in v:
            if item not in valid:
                raise ValueError(f"invalid status: {item}")
        return v


class ReportSetSimilarRequest(BaseModel):
    report_ids: list[str]
    n: int = 5

    @field_validator("report_ids")
    @classmethod
    def report_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("report_ids must contain at least one report id")
        return v

    @field_validator("n")
    @classmethod
    def n_range(cls, v: int) -> int:
        if not (1 <= v <= 50):
            raise ValueError("n must be 1-50")
        return v


class ReportQueryItem(ReportResponse):
    score: float | None = None


class ReportQueryResponse(BaseModel):
    items: list[ReportQueryItem]
    total: int
    limit: int
    offset: int
    ranked_by: str


class ReportFiltersQuery(BaseModel):
    """Query parameters for GET /reports/geojson -- use via Depends()"""

    type_id: str | None = None
    urgency: str | None = None
    status: str | None = None
    author_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    bbox: str | None = None  # "minLat,minLon,maxLat,maxLon"
