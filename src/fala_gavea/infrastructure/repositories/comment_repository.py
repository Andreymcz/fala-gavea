from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.comment import Comment
from fala_gavea.domain.repositories.comment_repository import ICommentRepository
from fala_gavea.infrastructure.database.models import CommentModel


class SQLAlchemyCommentRepository(ICommentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, comment: Comment) -> Comment:
        model = CommentModel(
            id=comment.id,
            forwarding_id=comment.forwarding_id,
            author_id=comment.author_id,
            text=comment.text,
            created_at=comment.created_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def delete(self, comment_id: str) -> None:
        model = self._session.get(CommentModel, comment_id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()

    def find_by_id(self, comment_id: str) -> Comment | None:
        model = self._session.get(CommentModel, comment_id)
        return self._to_entity(model) if model else None

    def list_by_forwarding(self, forwarding_id: str) -> list[Comment]:
        stmt = (
            select(CommentModel)
            .where(CommentModel.forwarding_id == forwarding_id)
            .order_by(CommentModel.created_at.asc())
        )
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def _to_entity(self, m: CommentModel) -> Comment:
        return Comment(
            id=m.id,
            forwarding_id=m.forwarding_id,
            author_id=m.author_id,
            text=m.text,
            created_at=m.created_at,
        )
