from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.anonymous_report_token import AnonymousReportToken
from fala_gavea.domain.repositories.anonymous_token_repository import IAnonymousTokenRepository
from fala_gavea.infrastructure.database.models import AnonymousReportTokenModel


class SQLAlchemyAnonymousTokenRepository(IAnonymousTokenRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, token: AnonymousReportToken) -> AnonymousReportToken:
        model = AnonymousReportTokenModel(
            id=token.id,
            token_hash=token.token_hash,
            report_id=token.report_id,
            created_at=token.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return AnonymousReportToken(
            id=model.id,
            token_hash=model.token_hash,
            report_id=model.report_id,
            created_at=model.created_at,
        )

    def find_report_ids_by_hash(self, token_hash: str) -> list[str]:
        stmt = select(AnonymousReportTokenModel.report_id).where(
            AnonymousReportTokenModel.token_hash == token_hash
        )
        return list(self._session.scalars(stmt).all())
