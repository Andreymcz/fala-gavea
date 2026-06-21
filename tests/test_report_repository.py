"""Unit tests for SQLAlchemyReportRepository multi-value filters and find_page."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fala_gavea.domain.entities.report import Report, Urgency
from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.repositories.report_repository import ReportFilters
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import (
    SQLAlchemyReportRepository,
)
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import (
    SQLAlchemyReportTypeRepository,
)
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report_type(db_session, name: str = "Tipo") -> str:
    rt = ReportType(
        id=str(uuid.uuid4()),
        name=name,
        description=None,
        active=True,
        created_at=datetime.now(UTC),
    )
    return SQLAlchemyReportTypeRepository(db_session).save(rt).id


def _make_author(db_session) -> str:
    ps = PasswordService()
    user = User(
        id=str(uuid.uuid4()),
        email=f"user-{uuid.uuid4()}@test.com",
        password_hash=ps.hash_password("pass1234"),
        name="Test User",
        role=UserRole.citizen,
        created_at=datetime.now(UTC),
    )
    return SQLAlchemyUserRepository(db_session).save(user).id


def _save_report(
    repo: SQLAlchemyReportRepository,
    *,
    text: str = "Buraco na calcada da esquina",
    lat: float = -22.97,
    lon: float = -43.22,
    urgency: Urgency = Urgency.media,
    report_type_id: str,
    author_id: str,
    created_at: datetime | None = None,
) -> Report:
    report = Report.create(
        text=text,
        lat=lat,
        lon=lon,
        urgency=urgency,
        report_type_id=report_type_id,
        author_id=author_id,
        created_at=created_at,
    )
    return repo.save(report)


# ---------------------------------------------------------------------------
# Tests: find_all with multi-value urgencies filter
# ---------------------------------------------------------------------------

def test_find_all_urgencies_in_filter(db_session) -> None:
    """find_all with urgencies=[alta, media] returns both and excludes baixa."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    _save_report(repo, urgency=Urgency.alta, report_type_id=rt_id, author_id=author_id, text="Alta urgencia aqui no local")
    _save_report(repo, urgency=Urgency.media, report_type_id=rt_id, author_id=author_id, text="Media urgencia neste ponto")
    _save_report(repo, urgency=Urgency.baixa, report_type_id=rt_id, author_id=author_id, text="Baixa urgencia no bairro")

    results = repo.find_all(ReportFilters(urgencies=[Urgency.alta, Urgency.media]))

    urgencies_found = {r.urgency for r in results}
    assert Urgency.alta in urgencies_found
    assert Urgency.media in urgencies_found
    assert Urgency.baixa not in urgencies_found
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Tests: find_all with report_type_ids IN filter
# ---------------------------------------------------------------------------

def test_find_all_report_type_ids_in_filter(db_session) -> None:
    """find_all with report_type_ids filters correctly."""
    rt_a = _make_report_type(db_session, "Iluminacao")
    rt_b = _make_report_type(db_session, "Transito")
    rt_c = _make_report_type(db_session, "Limpeza")
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    _save_report(repo, report_type_id=rt_a, author_id=author_id, text="Poste apagado na rua principal aqui")
    _save_report(repo, report_type_id=rt_b, author_id=author_id, text="Semaforo quebrado na avenida central")
    _save_report(repo, report_type_id=rt_c, author_id=author_id, text="Lixo acumulado na calcada do parque")

    results = repo.find_all(ReportFilters(report_type_ids=[rt_a, rt_b]))

    ids_found = {r.report_type_id for r in results}
    assert ids_found == {rt_a, rt_b}
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Tests: find_all text ilike search
# ---------------------------------------------------------------------------

def test_find_all_text_ilike_case_insensitive(db_session) -> None:
    """find_all text filter matches case-insensitively."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    _save_report(repo, text="Buraco na Esquina da rua principal", report_type_id=rt_id, author_id=author_id)
    _save_report(repo, text="ESQUINA com calcada danificada aqui", report_type_id=rt_id, author_id=author_id)
    _save_report(repo, text="Poste apagado no meio da avenida longa", report_type_id=rt_id, author_id=author_id)

    results = repo.find_all(ReportFilters(text="esquina"))

    assert len(results) == 2
    for r in results:
        assert "esquina" in r.text.lower()


# ---------------------------------------------------------------------------
# Tests: find_page order="recent" + pagination
# ---------------------------------------------------------------------------

def test_find_page_recent_order_and_total(db_session) -> None:
    """find_page returns newest-first and correct total."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    base = datetime(2024, 1, 1, tzinfo=UTC)
    _save_report(repo, text="Primeiro relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base)
    r2 = _save_report(repo, text="Segundo relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base + timedelta(hours=1))
    r3 = _save_report(repo, text="Terceiro relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base + timedelta(hours=2))

    page, total = repo.find_page(ReportFilters(), limit=2, offset=0, order="recent")

    assert total == 3
    assert len(page) == 2
    # newest first: r3, r2
    assert page[0].id == r3.id
    assert page[1].id == r2.id


def test_find_page_offset(db_session) -> None:
    """find_page with offset skips rows correctly."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    base = datetime(2024, 1, 1, tzinfo=UTC)
    _save_report(repo, text="Primeiro relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base)
    r2 = _save_report(repo, text="Segundo relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base + timedelta(hours=1))
    _save_report(repo, text="Terceiro relato registrado na area", report_type_id=rt_id, author_id=author_id, created_at=base + timedelta(hours=2))

    page, total = repo.find_page(ReportFilters(), limit=2, offset=1, order="recent")

    assert total == 3
    assert len(page) == 2
    # offset 1 from newest: r2, r1
    assert page[0].id == r2.id


# ---------------------------------------------------------------------------
# Tests: candidate_cap
# ---------------------------------------------------------------------------

def test_find_page_candidate_cap_limits_rows(db_session) -> None:
    """When candidate_cap < limit, only candidate_cap rows are returned."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    for i in range(5):
        _save_report(
            repo,
            text=f"Relato numero {i} registrado na calcada da area",
            report_type_id=rt_id,
            author_id=author_id,
        )

    # candidate_cap=3 should cap the returned rows even though limit=10
    page, total = repo.find_page(ReportFilters(), limit=10, offset=0, candidate_cap=3)

    assert total == 5
    assert len(page) == 3


def test_find_page_candidate_cap_no_effect_when_fewer_than_cap(db_session) -> None:
    """When total rows < candidate_cap, all matching rows are returned."""
    rt_id = _make_report_type(db_session)
    author_id = _make_author(db_session)
    repo = SQLAlchemyReportRepository(db_session)

    for i in range(3):
        _save_report(
            repo,
            text=f"Relato numero {i} registrado na calcada da area",
            report_type_id=rt_id,
            author_id=author_id,
        )

    page, total = repo.find_page(ReportFilters(), limit=10, offset=0, candidate_cap=500)

    assert total == 3
    assert len(page) == 3
