from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from fala_gavea.application.use_cases.comments.add_comment import AddCommentUseCase
from fala_gavea.application.use_cases.comments.delete_comment import DeleteCommentUseCase
from fala_gavea.application.use_cases.comments.list_comments import ListCommentsUseCase
from fala_gavea.domain.entities.comment import Comment
from fala_gavea.domain.entities.forwarding import Forwarding, ForwardingStatus
from fala_gavea.domain.exceptions import ForwardingNotFoundError, InvalidInputError, PermissionDeniedError


def _make_forwarding(fwd_id: str = "fwd-1") -> Forwarding:
    return Forwarding(
        id=fwd_id,
        institution="Comlurb",
        proposed_solution="Clean the street",
        status=ForwardingStatus.aguardando_solucao,
        agent_id="agent-1",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_comment(fwd_id: str = "fwd-1", author_id: str = "user-1") -> Comment:
    return Comment(
        id=str(uuid4()),
        forwarding_id=fwd_id,
        author_id=author_id,
        text="Bom trabalho",
        created_at=datetime.now(UTC),
    )


# --- AddCommentUseCase ---

def test_add_comment_success():
    comment_repo = MagicMock()
    forwarding_repo = MagicMock()
    forwarding_repo.find_by_id.return_value = _make_forwarding()
    comment_repo.add.side_effect = lambda c: c

    uc = AddCommentUseCase(comment_repo, forwarding_repo)
    result = uc.execute("fwd-1", "user-1", "Ótimo encaminhamento!")

    assert result.forwarding_id == "fwd-1"
    assert result.author_id == "user-1"
    assert result.text == "Ótimo encaminhamento!"
    comment_repo.add.assert_called_once()


def test_add_comment_forwarding_not_found():
    comment_repo = MagicMock()
    forwarding_repo = MagicMock()
    forwarding_repo.find_by_id.return_value = None

    uc = AddCommentUseCase(comment_repo, forwarding_repo)
    with pytest.raises(ForwardingNotFoundError):
        uc.execute("ghost-fwd", "user-1", "Comentário")


def test_add_comment_text_too_long():
    comment_repo = MagicMock()
    forwarding_repo = MagicMock()
    forwarding_repo.find_by_id.return_value = _make_forwarding()

    uc = AddCommentUseCase(comment_repo, forwarding_repo)
    with pytest.raises(InvalidInputError):
        uc.execute("fwd-1", "user-1", "x" * 501)


def test_add_comment_empty_text():
    comment_repo = MagicMock()
    forwarding_repo = MagicMock()
    forwarding_repo.find_by_id.return_value = _make_forwarding()

    uc = AddCommentUseCase(comment_repo, forwarding_repo)
    with pytest.raises(InvalidInputError):
        uc.execute("fwd-1", "user-1", "   ")


# --- DeleteCommentUseCase ---

def test_delete_comment_by_owner():
    comment_repo = MagicMock()
    comment = _make_comment(author_id="user-1")
    comment_repo.find_by_id.return_value = comment

    uc = DeleteCommentUseCase(comment_repo)
    uc.execute(comment.id, "user-1", "citizen")

    comment_repo.delete.assert_called_once_with(comment.id)


def test_delete_comment_by_agent():
    comment_repo = MagicMock()
    comment = _make_comment(author_id="user-1")
    comment_repo.find_by_id.return_value = comment

    uc = DeleteCommentUseCase(comment_repo)
    uc.execute(comment.id, "agent-99", "agent")

    comment_repo.delete.assert_called_once()


def test_delete_comment_forbidden():
    comment_repo = MagicMock()
    comment = _make_comment(author_id="user-1")
    comment_repo.find_by_id.return_value = comment

    uc = DeleteCommentUseCase(comment_repo)
    with pytest.raises(PermissionDeniedError):
        uc.execute(comment.id, "user-2", "citizen")


def test_delete_comment_not_found():
    comment_repo = MagicMock()
    comment_repo.find_by_id.return_value = None

    uc = DeleteCommentUseCase(comment_repo)
    with pytest.raises(ForwardingNotFoundError):
        uc.execute("ghost-id", "user-1", "citizen")


# --- ListCommentsUseCase ---

def test_list_comments_returns_list():
    comment_repo = MagicMock()
    comments = [_make_comment(), _make_comment()]
    comment_repo.list_by_forwarding.return_value = comments

    uc = ListCommentsUseCase(comment_repo)
    result = uc.execute("fwd-1")

    assert result == comments
    comment_repo.list_by_forwarding.assert_called_once_with("fwd-1")
