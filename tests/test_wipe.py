"""Tests for WipeDatabase use case."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime


from fala_gavea.application.use_cases.admin.wipe_database import WipeDatabase
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from sqlalchemy import text


def _make_user(db_session) -> User:
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email=f"u{uuid.uuid4()}@test.com",
        password_hash=ps.hash_password("pass"),
        name="User",
        role=UserRole.citizen,
        created_at=datetime.now(UTC),
    )
    return SQLAlchemyUserRepository(db_session).save(user)


def _make_report_type(db_session) -> ReportType:
    rt = ReportType(
        id=str(uuid.uuid4()),
        name=f"Tipo {uuid.uuid4()}",
        description=None,
        active=True,
        created_at=datetime.now(UTC),
    )
    return SQLAlchemyReportTypeRepository(db_session).save(rt)


def _make_report(db_session, user: User, rt: ReportType) -> Report:
    r = Report(
        id=str(uuid.uuid4()),
        text="Texto de relato suficientemente longo para passar",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.baixa,
        photo_url=None,
        report_type_id=rt.id,
        author_id=user.id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )
    return SQLAlchemyReportRepository(db_session).save(r)


def test_wipe_clears_reports_and_forwardings(db_session) -> None:
    user = _make_user(db_session)
    rt = _make_report_type(db_session)
    _make_report(db_session, user, rt)
    _make_report(db_session, user, rt)

    result = WipeDatabase().execute(db_session)

    assert result.reports == 2
    assert db_session.execute(text("SELECT COUNT(*) FROM reports")).scalar() == 0
    assert db_session.execute(text("SELECT COUNT(*) FROM report_types")).scalar() == 1


def test_wipe_with_report_types(db_session) -> None:
    user = _make_user(db_session)
    rt = _make_report_type(db_session)
    _make_report(db_session, user, rt)

    result = WipeDatabase().execute(db_session, include_report_types=True)

    assert result.reports == 1
    assert result.report_types == 1
    assert db_session.execute(text("SELECT COUNT(*) FROM report_types")).scalar() == 0


def test_wipe_preserves_users(db_session) -> None:
    _make_user(db_session)
    _make_user(db_session)

    WipeDatabase().execute(db_session, include_report_types=True)

    count = db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()
    assert count == 2
