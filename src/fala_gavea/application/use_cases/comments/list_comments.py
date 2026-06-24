from __future__ import annotations

from fala_gavea.domain.entities.comment import Comment
from fala_gavea.domain.repositories.comment_repository import ICommentRepository


class ListCommentsUseCase:
    def __init__(self, comment_repo: ICommentRepository) -> None:
        self._comment_repo = comment_repo

    def execute(self, forwarding_id: str) -> list[Comment]:
        return self._comment_repo.list_by_forwarding(forwarding_id)
