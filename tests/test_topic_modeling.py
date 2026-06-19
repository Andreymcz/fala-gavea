from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from fala_gavea.application.use_cases.topics.get_topics_for_reports import GetTopicsForReports
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency
from fala_gavea.domain.repositories.semantic_ports import ITopicModelPort
from fala_gavea.presentation.api.dependencies import get_topic_model_port


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(text: str = "Relato de teste sobre a rua") -> Report:
    return Report(
        id=str(uuid.uuid4()),
        text=text,
        lat=-22.9731,
        lon=-43.2272,
        urgency=Urgency.alta,
        status=ReportStatus.pendente,
        report_type_id=str(uuid.uuid4()),
        author_id=str(uuid.uuid4()),
        photo_url=None,
        created_at=datetime.now(UTC),
    )


class _FakeTopicPort(ITopicModelPort):
    """Fake ITopicModelPort with controllable infer_topics return value."""

    def __init__(self, result: list[dict] | None = None) -> None:
        self._result = result or []
        self.called_with: list[Report] | None = None

    def topic_of(self, report: Report) -> int:  # pragma: no cover
        return 0

    def list_topics(self) -> list[dict]:  # pragma: no cover
        return []

    def fit(self, reports: list[Report]) -> None:  # pragma: no cover
        pass

    def infer_topics(self, reports: list[Report]) -> list[dict]:
        self.called_with = reports
        return self._result


# ---------------------------------------------------------------------------
# Unit tests — use case layer
# ---------------------------------------------------------------------------

def test_infer_topics_empty_list_returns_empty() -> None:
    """quando infer_topics recebe lista vazia, retorna lista vazia."""
    port = _FakeTopicPort(result=[])
    result = port.infer_topics([])
    assert result == []


def test_use_case_corpus_too_small_returns_empty_without_calling_port() -> None:
    """quando corpus < min_docs (ex: 2 reports), GetTopicsForReports retorna lista vazia sem chamar port."""
    port = _FakeTopicPort(result=[{"topic_id": 0, "terms": ["buraco"], "count": 2}])
    reports = [_make_report(), _make_report()]  # 2 < default min_docs=3
    result = GetTopicsForReports(port, min_docs=3).execute(reports)
    assert result == []
    assert port.called_with is None, "infer_topics should NOT have been called"


def test_use_case_corpus_sufficient_calls_port_and_returns_result() -> None:
    """quando corpus >= min_docs, GetTopicsForReports chama infer_topics e retorna resultado do port."""
    expected = [{"topic_id": 0, "terms": ["buraco", "rua"], "count": 3}]
    port = _FakeTopicPort(result=expected)
    reports = [_make_report(), _make_report(), _make_report()]
    result = GetTopicsForReports(port, min_docs=3).execute(reports)
    assert result == expected
    assert port.called_with == reports


# ---------------------------------------------------------------------------
# Integration tests — HTTP layer
# ---------------------------------------------------------------------------

def test_get_topics_no_topic_port_returns_503(client: TestClient) -> None:
    """GET /reports/topics com topic_port=None retorna 503."""
    client.app.dependency_overrides[get_topic_model_port] = lambda: None
    # Need auth — register and login a citizen
    client.post("/auth/register", json={"email": "u503@test.com", "password": "pass1234", "name": "U503"})
    resp = client.post("/auth/token", data={"username": "u503@test.com", "password": "pass1234"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    result = client.get("/reports/topics", headers=headers)
    assert result.status_code == 503


def test_get_topics_zero_reports_returns_200_empty(
    client: TestClient, citizen_headers: dict
) -> None:
    """GET /reports/topics com 0 relatos filtrados retorna 200 com topics=[]."""
    port = _FakeTopicPort(result=[])
    client.app.dependency_overrides[get_topic_model_port] = lambda: port

    resp = client.get("/reports/topics", headers=citizen_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["topics"] == []
    assert data["total_reports"] == 0


def test_get_topics_no_auth_returns_401(client: TestClient) -> None:
    """GET /reports/topics sem auth retorna 401."""
    port = _FakeTopicPort()
    client.app.dependency_overrides[get_topic_model_port] = lambda: port

    resp = client.get("/reports/topics")
    assert resp.status_code == 401
