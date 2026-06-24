from __future__ import annotations

from fala_gavea.domain.exceptions import ForwardingNotFoundError, PermissionDeniedError
from fala_gavea.domain.repositories.comment_repository import ICommentRepository


class DeleteCommentUseCase:
    def __init__(self, comment_repo: ICommentRepository) -> None:
        self._comment_repo = comment_repo

    def execute(self, comment_id: str, requestor_id: str, requestor_role: str) -> None:
        comment = self._comment_repo.find_by_id(comment_id)
        if comment is None:
            raise ForwardingNotFoundError(comment_id)

        if requestor_role not in ("agent", "admin") and comment.author_id != requestor_id:
            raise PermissionDeniedError("You do not have permission to delete this comment")

        self._comment_repo.delete(comment_id)
