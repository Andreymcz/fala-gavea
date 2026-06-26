from __future__ import annotations

from fala_gavea.application.use_cases.help.answer_help_with_rag import (
    AnswerHelpWithRag,
    CitedDoc,
    HelpAnswer,
)
from fala_gavea.domain.repositories.doc_ports import DocChunk, DocSearchHit, IDocSearchPort
from fala_gavea.domain.repositories.semantic_ports import ILLMClient


class FakeDocSearchPort(IDocSearchPort):
    def __init__(self, hits: list[DocSearchHit]) -> None:
        self._hits = hits
        self.received_query: str | None = None
        self.received_roles: list[str] | None = None
        self.received_n: int | None = None

    def search(self, query: str, *, roles: list[str], n: int = 5) -> list[DocSearchHit]:
        self.received_query = query
        self.received_roles = roles
        self.received_n = n
        return self._hits

    def ready(self) -> bool:
        return True


class FakeLLMClient(ILLMClient):
    def __init__(self, reply: str = "resposta do llm") -> None:
        self._reply = reply
        self.call_count = 0
        self.received_system: str | None = None
        self.received_messages: list[dict[str, str]] | None = None

    def complete(self, system: str, messages: list[dict[str, str]]) -> str:
        self.call_count += 1
        self.received_system = system
        self.received_messages = messages
        return self._reply


def _chunk(
    chunk_index: int,
    text: str,
    source_path: str = "product-design/project/standards.md",
    section_title: str = "Testing",
) -> DocChunk:
    return DocChunk(
        chunk_id=f"{source_path}#{chunk_index}",
        text=text,
        source_path=source_path,
        doc_type="design",
        section_title=section_title,
        chunk_index=chunk_index,
        role_visibility="public",
    )


def test_hits_present_populate_cited_docs_and_ground_system_prompt() -> None:
    hits = [
        DocSearchHit(_chunk(0, "Como registrar um relato na plataforma.", "docs/a.md", "Relatos"), 0.91),
        DocSearchHit(_chunk(1, "Como criar um encaminhamento.", "docs/b.md", "Encaminhamentos"), 0.42),
    ]
    search = FakeDocSearchPort(hits)
    llm = FakeLLMClient(reply="aqui esta a resposta")
    use_case = AnswerHelpWithRag(search, llm)

    result = use_case.execute("como uso a plataforma?", roles=["public"])

    assert isinstance(result, HelpAnswer)
    assert result.response == "aqui esta a resposta"
    assert result.cited_docs == [
        CitedDoc("docs/a.md", "Relatos", 0.91),
        CitedDoc("docs/b.md", "Encaminhamentos", 0.42),
    ]
    # System prompt must contain each chunk's text and the untrusted-data delimiter.
    assert llm.call_count == 1
    assert llm.received_system is not None
    assert "<DOCUMENTOS>" in llm.received_system
    assert "</DOCUMENTOS>" in llm.received_system
    assert "Como registrar um relato na plataforma." in llm.received_system
    assert "Como criar um encaminhamento." in llm.received_system
    # User message forwarded as the single user turn.
    assert llm.received_messages == [{"role": "user", "content": "como uso a plataforma?"}]


def test_no_hits_returns_not_found_without_calling_llm() -> None:
    search = FakeDocSearchPort([])
    llm = FakeLLMClient()
    use_case = AnswerHelpWithRag(search, llm)

    result = use_case.execute("pergunta sem contexto", roles=["public"])

    assert result.cited_docs == []
    assert result.response == (
        "Não encontrei essa informação na documentação da plataforma Fala-Gávea."
    )
    assert llm.call_count == 0


def test_roles_forwarded_verbatim_to_search_port() -> None:
    search = FakeDocSearchPort([DocSearchHit(_chunk(0, "texto"), 0.5)])
    llm = FakeLLMClient()
    use_case = AnswerHelpWithRag(search, llm, top_k=7)

    use_case.execute("pergunta", roles=["agent", "admin"])

    assert search.received_roles == ["agent", "admin"]
    assert search.received_query == "pergunta"
    assert search.received_n == 7
