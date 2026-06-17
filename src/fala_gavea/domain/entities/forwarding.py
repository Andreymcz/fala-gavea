from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ForwardingStatus(str, Enum):
    aguardando_solucao = "aguardando_solucao"
    solucao_em_andamento = "solucao_em_andamento"
    finalizado = "finalizado"


@dataclass
class Forwarding:
    id: str
    institution: str
    proposed_solution: str
    status: ForwardingStatus
    agent_id: str
    created_at: datetime
    updated_at: datetime
