from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock, call

import pytest

from fala_gavea.application.use_cases.reports.bulk_create_reports import BulkCreateReports, BulkResult
from fala_gavea.domain.entities.report import Report, Urgency, ReportStatus
from fala_gavea.domain.entities.report_type import ReportType


def _make_rt(name: str = "Iluminacao") -> ReportType:
    return ReportType(id="rt-1", name=name, description=None, active=True, created_at=datetime.now(UTC))


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
    report_type_repo = MagicMock()
    report_type_repo.find_by_name.return_value = rt
    report_repo = MagicMock()
    report_repo.save.side_effect = lambda r: r  # return the same report
    return report_type_repo, report_repo


class TestBulkCreateReports:
    def test_inserts_valid_rows(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada na esquina", "lat": -22.97, "lon": -43.22},
            {"topico": "Iluminacao", "descricao": "Poste sem luz na avenida", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert result.inserted == 2
        assert result.skipped == 0
        assert result.errors == []
        assert report_repo.save.call_count == 2

    def test_skips_unknown_topico(self):
        report_type_repo, report_repo = _make_repos(None)
        rows = [
            {"topico": "Inexistente", "descricao": "Alguma descricao valida", "lat": -22.97, "lon": -43.22},
        ]
        uc = BulkCreateReports()
        result = uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert result.inserted == 0
        assert result.skipped == 1
        assert len(result.errors) == 1
        assert result.errors[0]["row"] == 0
        report_repo.save.assert_not_called()

    def test_mixed_valid_and_invalid(self):
        rt = _make_rt()
        report_type_repo = MagicMock()
        report_type_repo.find_by_name.side_effect = lambda name: rt if name == "Iluminacao" else None
        report_repo = MagicMock()
        report_repo.save.side_effect = lambda r: r

        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada perto da praca", "lat": -22.97, "lon": -43.22},
            {"topico": "Inexistente", "descricao": "Outro relato qualquer valido", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert result.inserted == 1
        assert result.skipped == 1

    def test_uses_created_at_from_row_when_datetime(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        ts = datetime(2024, 3, 15, 10, 0, 0)
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada perto do parque", "lat": -22.97, "lon": -43.22, "data": ts},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert len(saved) == 1
        assert saved[0].created_at == ts

    def test_uses_created_at_from_row_when_isoformat_string(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada na praca central", "lat": -22.97, "lon": -43.22, "data": "2024-03-15T10:00:00"},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert len(saved) == 1
        assert saved[0].created_at == datetime(2024, 3, 15, 10, 0, 0)

    def test_urgency_is_always_media(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada na travessa", "lat": -22.97, "lon": -43.22},
        ]
        saved: list[Report] = []
        report_repo.save.side_effect = lambda r: saved.append(r) or r

        uc = BulkCreateReports()
        uc.execute(rows, "user-1", report_type_repo, report_repo)

        assert saved[0].urgency == Urgency.media

    def test_indexer_called_for_each_saved_report(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        indexer = MagicMock()
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada no largo", "lat": -22.97, "lon": -43.22},
            {"topico": "Iluminacao", "descricao": "Poste apagado na alameda", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        uc.execute(rows, "user-1", report_type_repo, report_repo, indexer)

        assert indexer.index.call_count == 2

    def test_indexer_failure_does_not_abort(self):
        rt = _make_rt()
        report_type_repo, report_repo = _make_repos(rt)
        indexer = MagicMock()
        indexer.index.side_effect = RuntimeError("chroma down")
        rows = [
            {"topico": "Iluminacao", "descricao": "Lampada queimada no beco", "lat": -22.97, "lon": -43.22},
            {"topico": "Iluminacao", "descricao": "Poste sem luz na rua lateral", "lat": -22.98, "lon": -43.23},
        ]
        uc = BulkCreateReports()
        result = uc.execute(rows, "user-1", report_type_repo, report_repo, indexer)

        # Both should still be saved despite indexer failures
        assert result.inserted == 2
        assert report_repo.save.call_count == 2

    def test_empty_rows_returns_zero_counts(self):
        report_type_repo, report_repo = _make_repos(None)
        uc = BulkCreateReports()
        result = uc.execute([], "user-1", report_type_repo, report_repo)

        assert result == BulkResult(inserted=0, skipped=0, errors=[])
