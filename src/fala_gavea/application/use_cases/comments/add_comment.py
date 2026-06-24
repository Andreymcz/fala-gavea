from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fala_gavea.domain.entities.comment import Comment
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError
from fala_gavea.domain.repositories.comment_repository import ICommentRepository
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository


class AddCommentUseCase:
    def __init__(
        self,
        comment_repo: ICommentRepository,
        forwarding_repo: IForwardingRepository,
    ) -> None:
        self._comment_repo = comment_repo
        self._forwarding_repo = forwarding_repo

    def execute(self, forwarding_id: str, author_id: str, text: str) -> Comment:
        forwarding = self._forwarding_repo.find_by_id(forwarding_id)
        if forwarding is None:
            raise ForwardingNotFoundError(forwarding_id)

        text = text.strip()
        if not (1 <= len(text) <= 500):
            raise InvalidInputError("text must be 1-500 characters")

        comment = Comment(
            id=str(uuid4()),
            forwarding_id=forwarding_id,
            author_id=author_id,
            text=text,
            created_at=datetime.now(timezone.utc),
        )
        return self._comment_repo.add(comment)
