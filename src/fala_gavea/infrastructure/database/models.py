from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
)

from .session import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SAEnum("citizen", "agent", "admin", name="user_role"), nullable=False)
    created_at = Column(DateTime, nullable=False)


class ReportTypeModel(Base):
    __tablename__ = "report_types"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False)


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    text = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    urgency = Column(SAEnum("alta", "media", "baixa", name="report_urgency"), nullable=False)
    photo_url = Column(String, nullable=True)
    report_type_id = Column(String, ForeignKey("report_types.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(
        SAEnum("pendente", "em_analise", "encaminhado", "resolvido", name="report_status"),
        nullable=False,
        server_default="pendente",
    )
    created_at = Column(DateTime, nullable=False)


class ForwardingModel(Base):
    __tablename__ = "forwardings"

    id = Column(String, primary_key=True)
    institution = Column(String, nullable=False)
    proposed_solution = Column(String, nullable=False)
    status = Column(
        SAEnum(
            "aguardando_solucao",
            "solucao_em_andamento",
            "finalizado",
            name="forwarding_status",
        ),
        nullable=False,
    )
    agent_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class ForwardingReportModel(Base):
    __tablename__ = "forwarding_reports"

    forwarding_id = Column(String, ForeignKey("forwardings.id"), primary_key=True)
    report_id = Column(String, ForeignKey("reports.id"), primary_key=True)

    __table_args__ = (PrimaryKeyConstraint("forwarding_id", "report_id"),)


class SavedFilterModel(Base):
    __tablename__ = "saved_filters"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    body = Column(String, nullable=False)
    schema_ver = Column(String, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
