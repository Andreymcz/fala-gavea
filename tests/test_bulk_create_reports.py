from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock

from fala_gavea.application.use_cases.reports.bulk_create_reports import (
    BulkCreateReports,
    BulkResult,
    _LAT_MAX,
    _LAT_MIN,
    _LON_MAX,
    _LON_MIN,
)
from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus
from fala_gavea.domain.entities.report_type import ReportType
from fala_gavea.domain.entities.user import User, UserRole


def _make_rt(name: str = "Iluminacao", rt_id: str = "rt-1") -> ReportType:
    return ReportType(id=rt_id, name=name, description=None, active=True, created_at=datetime.now(UTC))


def _make_report(report_type_id: str = "rt-1") -> Report:
    return Report(
        id="r-1",
        text="Lampada queimada na rua principal",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.media,
        photo_url=None,
        report_type_id=report_type_id,
        author_id="user-1",
        status=ReportStatus.pendente,
        created_at=datetime.now(UTC),
    )


def _make_repos(rt: ReportType | None = None):
    """Build fake repos + services for the new BulkCreateReports signature.

    - report_type_repo.find_by_name -> rt (None triggers auto-create path)
    - report_type_repo.save echoes the ReportType (used by CreateReportType)
    - report_repo.save echoes the report
    - user_repo.find_by_email -> None (so a synthetic user is created the first time)
    - user_repo.save echoes the user
    - password_service.hash_password -> fixed hash
    """
    report_type_repo = MagicMock()
    report_type_repo.find_by_name.return_value = rt
    report_type_repo.save.side_effect = lambda r: r
    report_repo = MagicMock()
    report_repo.save.side_effect = lambda r: r
    user_repo = MagicMock()
    user_repo.find_by_email.return_value = None
    user_repo.save.side_effect = lambda u: u
    password_service = MagicMock()
    password_service.hash_password.return_value = "hashed"
    return report_type_repo, report_repo, user_repo, password_service


class TestBulkCreateReports:
    def test_inserts_valid_rows(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Lampada queimada na esquina", "lat": -22.97, "lon": -43.22},
            {"user_id": "u2", "topico": "Iluminacao", "descricao": "Poste sem luz na avenida", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result.inserted == 2
        assert result.skipped == 0
        assert result.errors == []
        assert report_repo.save.call_count == 2

    def test_creates_user_once_and_reuses_for_same_user_id(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Primeiro relato do cidadao", "lat": -22.97, "lon": -43.22},
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Segundo relato do mesmo cidadao", "lat": -22.98, "lon": -43.23},
        ]
        saved_users: list[User] = []
        user_repo.save.side_effect = lambda u: saved_users.append(u) or u
        saved_reports: list[Report] = []
        report_repo.save.side_effect = lambda r: saved_reports.append(r) or r

        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result.inserted == 2
        # Only one user created despite two rows with the same user_id (cache + dedup).
        assert len(saved_users) == 1
        assert saved_users[0].email == "u1@seed.gavea.br"
        assert saved_users[0].name == "Cidadão u1"
        assert saved_users[0].role == UserRole.citizen
        # find_by_email only consulted once (second row served from cache).
        assert user_repo.find_by_email.call_count == 1
        # Both reports reference the same synthetic author.
        assert saved_reports[0].author_id == saved_reports[1].author_id == saved_users[0].id

    def test_reuses_existing_user_by_synthetic_email(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        existing = User.create(
            email="u9@seed.gavea.br",
            password_hash="already-set",
            name="Cidadão u9",
            role=UserRole.citizen,
        )
        user_repo.find_by_email.return_value = existing
        rows = [
            {"user_id": "u9", "topico": "Iluminacao", "descricao": "Relato de usuario existente", "lat": -22.97, "lon": -43.22},
        ]
        saved_reports: list[Report] = []
        report_repo.save.side_effect = lambda r: saved_reports.append(r) or r

        uc = BulkCreateReports()
        uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        # Existing account reused, never re-saved (password not overwritten).
        user_repo.save.assert_not_called()
        assert saved_reports[0].author_id == existing.id

    def test_skips_row_without_user_id(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "", "topico": "Iluminacao", "descricao": "Sem autor", "lat": -22.97, "lon": -43.22},
        ]
        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result.inserted == 0
        assert result.skipped == 1
        assert result.errors[0]["row"] == 0
        assert "user_id" in result.errors[0]["reason"]
        report_repo.save.assert_not_called()

    def test_auto_creates_unknown_topico(self):
        # find_by_name returns None -> topic is auto-created via CreateReportType.
        report_type_repo, report_repo, user_repo, password_service = _make_repos(None)
        created_rt = _make_rt(name="Novo Topico", rt_id="rt-new")
        report_type_repo.save.side_effect = lambda r: created_rt
        rows = [
            {"user_id": "u1", "topico": "Novo Topico", "descricao": "Relato com topico inexistente", "lat": -22.97, "lon": -43.22},
        ]
        saved_reports: list[Report] = []
        report_repo.save.side_effect = lambda r: saved_reports.append(r) or r

        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result.inserted == 1
        report_type_repo.save.assert_called_once()
        assert saved_reports[0].report_type_id == "rt-new"

    def test_skips_topico_too_short_without_aborting_batch(self):
        rt = _make_rt()
        # First row: valid existing topic; second row: invalid <3-char topic (must be auto-created -> fails validation).
        report_type_repo, report_repo, user_repo, password_service = _make_repos(None)
        report_type_repo.find_by_name.side_effect = lambda name: rt if name == "Iluminacao" else None
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Relato valido com topico ok", "lat": -22.97, "lon": -43.22},
            {"user_id": "u2", "topico": "ab", "descricao": "Relato com topico curto demais", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        # Batch did not abort: first row inserted, invalid-topic row skipped with error.
        assert result.inserted == 1
        assert result.skipped == 1
        assert result.errors[0]["row"] == 1
        assert "topico" in result.errors[0]["reason"]

    def test_urgency_read_from_row_and_falls_back_to_media(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Relato urgente de verdade", "lat": -22.97, "lon": -43.22, "urgency": "alta"},
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Relato com urgencia invalida", "lat": -22.98, "lon": -43.23, "urgency": "urgentissimo"},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert saved[0].urgency == Urgency.alta
        assert saved[1].urgency == Urgency.media

    def test_generates_random_coords_in_gavea_bbox_when_missing(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Relato sem coordenadas validas"},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result.inserted == 1
        assert _LAT_MIN <= saved[0].lat <= _LAT_MAX
        assert _LON_MIN <= saved[0].lon <= _LON_MAX

    def test_uses_created_at_from_row_when_datetime(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        ts = datetime(2024, 3, 15, 10, 0, 0)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Lampada queimada perto do parque", "lat": -22.97, "lon": -43.22, "data": ts},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert len(saved) == 1
        assert saved[0].created_at == ts

    def test_uses_created_at_from_row_when_isoformat_string(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Lampada queimada na praca central", "lat": -22.97, "lon": -43.22, "data": "2024-03-15T10:00:00"},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert len(saved) == 1
        assert saved[0].created_at == datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)

    def test_indexer_called_for_each_saved_report(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        indexer = MagicMock()
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Lampada queimada no largo", "lat": -22.97, "lon": -43.22},
            {"user_id": "u2", "topico": "Iluminacao", "descricao": "Poste apagado na alameda", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
            indexer=indexer,
        )

        assert indexer.index.call_count == 2

    def test_indexer_failure_does_not_abort(self):
        rt = _make_rt()
        report_type_repo, report_repo, user_repo, password_service = _make_repos(rt)
        indexer = MagicMock()
        indexer.index.side_effect = RuntimeError("chroma down")
        rows = [
            {"user_id": "u1", "topico": "Iluminacao", "descricao": "Lampada queimada no beco", "lat": -22.97, "lon": -43.22},
            {"user_id": "u2", "topico": "Iluminacao", "descricao": "Poste sem luz na rua lateral", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(
            rows,
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
            indexer=indexer,
        )

        # Both should still be saved despite indexer failures
        assert result.inserted == 2
        assert report_repo.save.call_count == 2

    def test_empty_rows_returns_zero_counts(self):
        report_type_repo, report_repo, user_repo, password_service = _make_repos(None)
        uc = BulkCreateReports()
        result = uc.execute(
            [],
            report_type_repo=report_type_repo,
            report_repo=report_repo,
            user_repo=user_repo,
            password_service=password_service,
        )

        assert result == BulkResult(inserted=0, skipped=0, errors=[])
