from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.comments.add_comment import AddCommentUseCase
from fala_gavea.application.use_cases.comments.delete_comment import DeleteCommentUseCase
from fala_gavea.application.use_cases.comments.list_comments import ListCommentsUseCase
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError, PermissionDeniedError
from fala_gavea.domain.repositories.comment_repository import ICommentRepository
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.presentation.api.dependencies import (
    get_comment_repo,
    get_current_user,
    get_forwarding_repo,
    get_optional_user,
)
from fala_gavea.presentation.schemas.comments import AddCommentRequest, CommentResponse

router = APIRouter()


@router.get("", response_model=list[CommentResponse])
def list_comments(
    forwarding_id: str,  # injected from path by FastAPI when router is mounted with path var
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    current_user: User | None = Depends(get_optional_user),
) -> list[CommentResponse]:
    # author_id is exposed only to authenticated callers; the public/unauthenticated
    # forwarding view must never reveal which user authored a comment.
    expose_author = current_user is not None
    comments = ListCommentsUseCase(comment_repo).execute(forwarding_id)
    return [CommentResponse(
        id=c.id,
        forwarding_id=c.forwarding_id,
        author_id=c.author_id if expose_author else None,
        text=c.text,
        created_at=c.created_at,
    ) for c in comments]


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment(
    forwarding_id: str,
    body: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
) -> CommentResponse:
    try:
        comment = AddCommentUseCase(comment_repo, forwarding_repo).execute(
            forwarding_id=forwarding_id,
            author_id=current_user.id,
            text=body.text,
        )
        return CommentResponse(
            id=comment.id,
            forwarding_id=comment.forwarding_id,
            author_id=comment.author_id,
            text=comment.text,
            created_at=comment.created_at,
        )
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    forwarding_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    comment_repo: ICommentRepository = Depends(get_comment_repo),
) -> None:
    try:
        DeleteCommentUseCase(comment_repo).execute(
            comment_id=comment_id,
            requestor_id=current_user.id,
            requestor_role=current_user.role.value,
        )
    except ForwardingNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
