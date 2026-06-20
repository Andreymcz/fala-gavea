"""Tests for BulkCreateReportTypes use case."""
from __future__ import annotations

from fala_gavea.application.use_cases.report_types.bulk_create_report_types import BulkCreateReportTypes
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository


def test_bulk_create_happy_path(db_session) -> None:
    repo = SQLAlchemyReportTypeRepository(db_session)
    rows = [
        {"nome": "Iluminacao publica", "descricao": "Problemas de iluminacao"},
        {"nome": "Buraco na via", "descricao": None},
        {"nome": "Lixo acumulado", "descricao": "Descarte irregular"},
    ]
    result = BulkCreateReportTypes().execute(rows, repo)
    assert result.inserted == 3
    assert result.skipped == 0
    assert result.errors == []


def test_bulk_create_duplicate_skipped(db_session) -> None:
    repo = SQLAlchemyReportTypeRepository(db_session)
    rows = [{"nome": "Iluminacao publica", "descricao": None}]
    BulkCreateReportTypes().execute(rows, repo)
    result = BulkCreateReportTypes().execute(rows, repo)
    assert result.inserted == 0
    assert result.skipped == 1


def test_bulk_create_invalid_name_length_in_errors(db_session) -> None:
    repo = SQLAlchemyReportTypeRepository(db_session)
    rows = [
        {"nome": "Ok", "descricao": None},  # too short (2 chars)
        {"nome": "Valido aqui", "descricao": None},
    ]
    result = BulkCreateReportTypes().execute(rows, repo)
    assert result.inserted == 1
    assert result.skipped == 1
    assert len(result.errors) == 1
    assert "3-100" in result.errors[0]["reason"]
