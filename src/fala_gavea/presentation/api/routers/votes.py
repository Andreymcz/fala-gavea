from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from fala_gavea.application.use_cases.votes.cast_vote import CastVoteUseCase
from fala_gavea.application.use_cases.votes.get_vote_summary import GetVoteSummaryUseCase
from fala_gavea.application.use_cases.votes.retract_vote import RetractVoteUseCase
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import (
    ForwardingNotFoundError,
    InvalidInputError,
    ReportNotFoundError,
    SelfVoteError,
)
from fala_gavea.domain.repositories.forwarding_repository import IForwardingRepository
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.vote_repository import IVoteRepository
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_forwarding_repo,
    get_optional_user,
    get_report_repo,
    get_vote_repo,
)
from fala_gavea.presentation.schemas.votes import CastVoteRequest, VoteSummarySchema

reports_votes_router = APIRouter()
forwardings_votes_router = APIRouter()
votes_summary_router = APIRouter()

limiter = Limiter(
    key_func=lambda request: str(
        getattr(request.state, "current_user_id", None) or get_remote_address(request)
    )
)


def _to_summary_schema(summary) -> VoteSummarySchema:
    return VoteSummarySchema(
        upvotes=summary.upvotes,
        downvotes=summary.downvotes,
        user_vote=summary.user_vote,
    )


# --- Report votes ---

@reports_votes_router.post("/{report_id}/votes", response_model=VoteSummarySchema, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def cast_vote_on_report(
    request: Request,
    report_id: str,
    body: CastVoteRequest,
    current_user: User = Depends(get_current_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
) -> VoteSummarySchema:
    use_case = CastVoteUseCase(vote_repo, report_repo, forwarding_repo)
    summary_uc = GetVoteSummaryUseCase(vote_repo)
    try:
        use_case.execute(current_user.id, "report", report_id, body.value)
    except ReportNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    except SelfVoteError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot vote on your own content")
    except InvalidInputError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    summary = summary_uc.execute("report", report_id, current_user.id)
    return _to_summary_schema(summary)


@reports_votes_router.delete("/{report_id}/votes", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def retract_vote_on_report(
    request: Request,
    report_id: str,
    current_user: User = Depends(get_current_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> None:
    use_case = RetractVoteUseCase(vote_repo)
    use_case.execute(current_user.id, "report", report_id)


# --- Forwarding votes ---

@forwardings_votes_router.post("/{forwarding_id}/votes", response_model=VoteSummarySchema, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
def cast_vote_on_forwarding(
    request: Request,
    forwarding_id: str,
    body: CastVoteRequest,
    current_user: User = Depends(get_current_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
    report_repo: IReportRepository = Depends(get_report_repo),
    forwarding_repo: IForwardingRepository = Depends(get_forwarding_repo),
) -> VoteSummarySchema:
    use_case = CastVoteUseCase(vote_repo, report_repo, forwarding_repo)
    summary_uc = GetVoteSummaryUseCase(vote_repo)
    try:
        use_case.execute(current_user.id, "forwarding", forwarding_id, body.value)
    except ForwardingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Forwarding not found")
    except SelfVoteError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot vote on your own content")
    except InvalidInputError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    summary = summary_uc.execute("forwarding", forwarding_id, current_user.id)
    return _to_summary_schema(summary)


@forwardings_votes_router.delete("/{forwarding_id}/votes", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def retract_vote_on_forwarding(
    request: Request,
    forwarding_id: str,
    current_user: User = Depends(get_current_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> None:
    use_case = RetractVoteUseCase(vote_repo)
    use_case.execute(current_user.id, "forwarding", forwarding_id)


# --- GET summary endpoints (optional auth) ---

@reports_votes_router.get("/{report_id}/votes", response_model=VoteSummarySchema)
def get_report_vote_summary(
    report_id: str,
    current_user: User | None = Depends(get_optional_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> VoteSummarySchema:
    use_case = GetVoteSummaryUseCase(vote_repo)
    summary = use_case.execute("report", report_id, current_user.id if current_user else None)
    return _to_summary_schema(summary)


@forwardings_votes_router.get("/{forwarding_id}/votes", response_model=VoteSummarySchema)
def get_forwarding_vote_summary(
    forwarding_id: str,
    current_user: User | None = Depends(get_optional_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> VoteSummarySchema:
    use_case = GetVoteSummaryUseCase(vote_repo)
    summary = use_case.execute("forwarding", forwarding_id, current_user.id if current_user else None)
    return _to_summary_schema(summary)


# --- Batch summary endpoint ---

@votes_summary_router.get("/reports/summary", response_model=dict[str, VoteSummarySchema])
def batch_report_vote_summaries(
    ids: str = Query(..., description="Comma-separated report IDs"),
    current_user: User | None = Depends(get_optional_user),
    vote_repo: IVoteRepository = Depends(get_vote_repo),
) -> dict[str, VoteSummarySchema]:
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        return {}
    if len(id_list) > 200:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Too many IDs (max 200)")
    summaries = vote_repo.get_summaries_batch("report", id_list, current_user.id if current_user else None)
    return {tid: _to_summary_schema(s) for tid, s in summaries.items()}
