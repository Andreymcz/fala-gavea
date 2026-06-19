from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fala_gavea.application.use_cases.chat.answer_with_rag import AnswerWithRag, RagAnswer
from fala_gavea.domain.entities.report import Report, ReportStatus, Urgency


def _make_report(report_id: str, text: str = "") -> Report:
    return Report(
        id=report_id,
        text=text or f"Texto do relato {report_id}",
        lat=-22.97,
        lon=-43.22,
        urgency=Urgency.alta,
        status=ReportStatus.pendente,
        report_type_id="rt-1",
        author_id="user-1",
        photo_url=None,
        created_at=datetime.now(timezone.utc),
    )


def _make_use_case(search_return, repo_side_effect, llm_return="resposta LLM"):
    search_port = MagicMock()
    search_port.search.return_value = search_return

    report_repo = MagicMock()
    report_repo.find_by_id.side_effect = repo_side_effect

    llm_client = MagicMock()
    llm_client.complete.return_value = llm_return

    return AnswerWithRag(search_port, report_repo, llm_client), search_port, report_repo, llm_client


# ---------------------------------------------------------------------------
# 1. Happy path with hits
# ---------------------------------------------------------------------------

def test_happy_path_with_hits():
    r1 = _make_report("r1", "Buraco na Rua das Flores")
    r2 = _make_report("r2", "Poste apagado na Marquês de São Vicente")

    uc, _, _, llm = _make_use_case(
        search_return=[("r1", 0.9), ("r2", 0.7)],
        repo_side_effect=lambda rid: {"r1": r1, "r2": r2}.get(rid),
        llm_return="Há dois relatos relevantes.",
    )

    result = uc.execute("buracos na rua")

    assert isinstance(result, RagAnswer)
    assert result.response == "Há dois relatos relevantes."
    assert result.cited_report_ids == ["r1", "r2"]

    # LLM must have been called with a system prompt that includes both report texts
    call_args = llm.complete.call_args
    system_prompt = call_args[0][0]
    assert "r1" in system_prompt
    assert "r2" in system_prompt
    assert "Buraco na Rua das Flores" in system_prompt
    assert "Poste apagado" in system_prompt

    # messages list must contain user message
    messages = call_args[0][1]
    assert messages == [{"role": "user", "content": "buracos na rua"}]


# ---------------------------------------------------------------------------
# 2. Empty semantic index
# ---------------------------------------------------------------------------

def test_empty_semantic_index():
    uc, _, report_repo, llm = _make_use_case(
        search_return=[],
        repo_side_effect=lambda rid: None,
        llm_return="Não encontrei relatos relevantes.",
    )

    result = uc.execute("calçada quebrada")

    assert result.cited_report_ids == []
    assert result.response == "Não encontrei relatos relevantes."

    # repo should not be called
    report_repo.find_by_id.assert_not_called()

    # system prompt must NOT contain a "Relatos relevantes" context block
    system_prompt = llm.complete.call_args[0][0]
    assert "Relatos relevantes encontrados:" not in system_prompt


# ---------------------------------------------------------------------------
# 3. Report not found in repo
# ---------------------------------------------------------------------------

def test_report_not_found_in_repo():
    """Search returns an id but find_by_id returns None — LLM still called, no crash."""
    uc, _, _, llm = _make_use_case(
        search_return=[("ghost-id", 0.8)],
        repo_side_effect=lambda rid: None,
        llm_return="Sem contexto.",
    )

    result = uc.execute("problema desconhecido")

    # cited_ids still includes the id from search (before hydration)
    assert result.cited_report_ids == ["ghost-id"]
    assert result.response == "Sem contexto."

    # system prompt falls back to bare prompt (no context block)
    system_prompt = llm.complete.call_args[0][0]
    assert "Relatos relevantes encontrados:" not in system_prompt


# ---------------------------------------------------------------------------
# 4. LLM raises
# ---------------------------------------------------------------------------

def test_llm_raises_propagates():
    search_port = MagicMock()
    search_port.search.return_value = []

    report_repo = MagicMock()
    report_repo.find_by_id.return_value = None

    llm_client = MagicMock()
    llm_client.complete.side_effect = RuntimeError("LLM offline")

    uc = AnswerWithRag(search_port, report_repo, llm_client)

    with pytest.raises(RuntimeError, match="LLM offline"):
        uc.execute("qualquer mensagem")
