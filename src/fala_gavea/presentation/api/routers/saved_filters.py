from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from fala_gavea.application.use_cases.saved_filters.create_saved_filter import CreateSavedFilter
from fala_gavea.application.use_cases.saved_filters.delete_saved_filter import DeleteSavedFilter
from fala_gavea.application.use_cases.saved_filters.get_saved_filter import GetSavedFilter
from fala_gavea.application.use_cases.saved_filters.list_saved_filters import ListSavedFilters
from fala_gavea.application.use_cases.saved_filters.update_saved_filter import UpdateSavedFilter
from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidInputError, SavedFilterNotFoundError
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository
from fala_gavea.presentation.api.dependencies import get_current_user, get_saved_filter_repo
from fala_gavea.presentation.schemas.saved_filter import (
    SavedFilterCreate,
    SavedFilterResponse,
    SavedFilterUpdate,
)

router = APIRouter()


def _to_response(sf: SavedFilter) -> SavedFilterResponse:
    body = json.loads(sf.body) if isinstance(sf.body, str) else sf.body
    return SavedFilterResponse(
        id=sf.id,
        name=sf.name,
        body=body,
        schema_ver=sf.schema_ver,
        created_at=sf.created_at,
        updated_at=sf.updated_at,
        deprecated_fields=[],
    )


@router.post("/", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    payload: SavedFilterCreate,
    current_user: User = Depends(get_current_user),
    repo: ISavedFilterRepository = Depends(get_saved_filter_repo),
) -> SavedFilterResponse:
    try:
        sf = CreateSavedFilter(repo).execute(
            owner_id=current_user.id,
            name=payload.name,
            body=json.dumps(payload.body),
        )
        return _to_response(sf)
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/", response_model=list[SavedFilterResponse])
def list_saved_filters(
    current_user: User = Depends(get_current_user),
    repo: ISavedFilterRepository = Depends(get_saved_filter_repo),
) -> list[SavedFilterResponse]:
    filters = ListSavedFilters(repo).execute(owner_id=current_user.id)
    return [_to_response(sf) for sf in filters]


@router.get("/{id}", response_model=SavedFilterResponse)
def get_saved_filter(
    id: str,
    current_user: User = Depends(get_current_user),
    repo: ISavedFilterRepository = Depends(get_saved_filter_repo),
) -> SavedFilterResponse:
    try:
        sf = GetSavedFilter(repo).execute(id=id, owner_id=current_user.id)
        return _to_response(sf)
    except SavedFilterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{id}", response_model=SavedFilterResponse)
def update_saved_filter(
    id: str,
    payload: SavedFilterUpdate,
    current_user: User = Depends(get_current_user),
    repo: ISavedFilterRepository = Depends(get_saved_filter_repo),
) -> SavedFilterResponse:
    try:
        body_str = json.dumps(payload.body) if payload.body is not None else None
        sf = UpdateSavedFilter(repo).execute(
            id=id,
            owner_id=current_user.id,
            name=payload.name,
            body=body_str,
        )
        return _to_response(sf)
    except SavedFilterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInputError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    id: str,
    current_user: User = Depends(get_current_user),
    repo: ISavedFilterRepository = Depends(get_saved_filter_repo),
) -> None:
    try:
        DeleteSavedFilter(repo).execute(id=id, owner_id=current_user.id)
    except SavedFilterNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
