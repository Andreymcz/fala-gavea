from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Integer, String

from .session import Base
from ...domain.entities.report import TerritoryLevel


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    territory_level = Column(SAEnum(TerritoryLevel), nullable=False)
    territory_name = Column(String, nullable=False)
    author_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    ai_labels = Column(JSON, nullable=False, default=list)
    label_feedback = Column(JSON, nullable=False, default=dict)
    likes_count = Column(Integer, nullable=False, default=0)
