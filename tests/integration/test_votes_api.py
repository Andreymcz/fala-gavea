from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_forwarding_repository import SQLAlchemyForwardingRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


def _make_citizen(db_session, email: str = "citizen2@test.com") -> tuple[User, str]:
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=ps.hash_password("pass1234"),
        name="Citizen",
        role=UserRole.citizen,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(user)
    return user, "pass1234"


def _auth_headers(client, email: str, password: str) -> dict:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_cast_and_retract_vote_on_report(client, db_session, sample_report_type, citizen_headers):
    # Create a report authored by a different user
    other_user, pwd = _make_citizen(db_session, "other@test.com")
    report = Report(
        id=str(uuid.uuid4()),
        text="Streetlight broken near park",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.media,
        photo_url=None,
        report_type_id=sample_report_type,
        author_id=other_user.id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyReportRepository(db_session).save(report)

    resp = client.post(f"/reports/{report.id}/votes", json={"value": 1}, headers=citizen_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["upvotes"] == 1
    assert data["user_vote"] == 1

    # Retract
    resp2 = client.delete(f"/reports/{report.id}/votes", headers=citizen_headers)
    assert resp2.status_code == 204


def test_self_vote_returns_409(client, db_session, sample_report_type, citizen_headers, citizen_token):
    from fala_gavea.infrastructure.auth.jwt_service import JWTService
    payload = JWTService().decode_token(citizen_token)
    citizen_id = payload["sub"]

    report = Report(
        id=str(uuid.uuid4()),
        text="My own report, should not vote",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        photo_url=None,
        report_type_id=sample_report_type,
        author_id=citizen_id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyReportRepository(db_session).save(report)

    resp = client.post(f"/reports/{report.id}/votes", json={"value": 1}, headers=citizen_headers)
    assert resp.status_code == 409


def test_vote_on_nonexistent_report_returns_404(client, citizen_headers):
    resp = client.post(f"/reports/{uuid.uuid4()}/votes", json={"value": 1}, headers=citizen_headers)
    assert resp.status_code == 404


def test_cast_vote_on_forwarding(client, db_session, sample_report_type, citizen_headers, agent_headers):
    # Create forwarding authored by agent
    other_user, pwd = _make_citizen(db_session, "fwd_voter@test.com")
    headers = _auth_headers(client, "fwd_voter@test.com", pwd)

    # Create agent user and forwarding
    ps = PasswordService()
    agent = User(
        id=str(uuid.uuid4()),
        email="agent2@test.com",
        password_hash=ps.hash_password("pass1234"),
        name="Agent2",
        role=UserRole.agent,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyUserRepository(db_session).save(agent)
    report = Report(
        id=str(uuid.uuid4()),
        text="Street flooding near corner",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        photo_url=None,
        report_type_id=sample_report_type,
        author_id=other_user.id,
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )
    SQLAlchemyReportRepository(db_session).save(report)
    fwd = Forwarding(
        id=str(uuid.uuid4()),
        institution="SEOP",
        proposed_solution="Send maintenance team to fix flooding",
        status=ForwardingStatus.aguardando_solucao,
        agent_id=agent.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    fwd_repo = SQLAlchemyForwardingRepository(db_session)
    fwd_repo.save(fwd)
    fwd_repo.add_reports(fwd.id, [report.id])

    resp = client.post(f"/forwardings/{fwd.id}/votes", json={"value": -1}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["downvotes"] == 1
    assert data["user_vote"] == -1
