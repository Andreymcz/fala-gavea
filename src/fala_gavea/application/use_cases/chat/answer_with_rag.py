from __future__ import annotations

from dataclasses import dataclass

from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.semantic_ports import ILLMClient, ISemanticSearchPort

_SYSTEM_PT_BR = (
    "Você é um assistente de exploração de demandas urbanas da Gávea. "
    "Responda sempre em português do Brasil. "
    "Use apenas as informações dos relatos fornecidos como contexto. "
    "Se não houver contexto suficiente, diga que não encontrou relatos relevantes. "
    "Não invente informações."
)

_TOP_K = 5


@dataclass
class RagAnswer:
    response: str
    cited_report_ids: list[str]


class AnswerWithRag:
    def __init__(
        self,
        search_port: ISemanticSearchPort,
        report_repo: IReportRepository,
        llm_client: ILLMClient,
        top_k: int = _TOP_K,
    ) -> None:
        self._search = search_port
        self._repo = report_repo
        self._llm = llm_client
        self._top_k = top_k

    def execute(self, message: str) -> RagAnswer:
        hits = self._search.search(message, n=self._top_k)
        cited_ids = [rid for rid, _score in hits]

        context_parts: list[str] = []
        for rid, score in hits:
            report = self._repo.find_by_id(rid)
            if report is not None:
                context_parts.append(
                    f"[{rid}] (score={score:.2f}) {report.text}"
                )

        if context_parts:
            context_block = "\n".join(context_parts)
            system = (
                f"{_SYSTEM_PT_BR}\n\n"
                f"Relatos relevantes encontrados:\n{context_block}"
            )
        else:
            system = _SYSTEM_PT_BR

        messages = [{"role": "user", "content": message}]
        reply = self._llm.complete(system, messages)
        return RagAnswer(response=reply, cited_report_ids=cited_ids)
