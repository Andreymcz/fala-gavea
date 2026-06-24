from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from pydantic import BaseModel

from fala_gavea.application.use_cases.auth.login_user import LoginUser
from fala_gavea.application.use_cases.auth.register_user import RegisterUser
from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from fala_gavea.presentation.api.dependencies import (
    get_current_user,
    get_jwt_service,
    get_password_service,
    get_user_repo,
    require_role,
)
from fala_gavea.presentation.schemas.auth import RegisterRequest, TokenResponse, UserResponse


class UserRoleUpdate(BaseModel):
    role: UserRole

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    user_repo=Depends(get_user_repo),
    password_service=Depends(get_password_service),
) -> UserResponse:
    try:
        user = RegisterUser(user_repo, password_service).execute(
            body.email, body.password, body.name
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            created_at=user.created_at,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/token", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    user_repo=Depends(get_user_repo),
    password_service=Depends(get_password_service),
    jwt_service=Depends(get_jwt_service),
) -> TokenResponse:
    try:
        token = LoginUser(user_repo, password_service, jwt_service).execute(
            form.username, form.password
        )
        return TokenResponse(access_token=token)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        created_at=current_user.created_at,
    )


@router.patch("/admin/users/{email}/role", response_model=UserResponse)
def change_user_role(
    email: str,
    body: UserRoleUpdate,
    _admin: User = Depends(require_role("admin")),
    user_repo=Depends(get_user_repo),
) -> UserResponse:
    user = user_repo.find_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found: {email}")
    user.role = body.role
    updated = user_repo.save(user)
    return UserResponse(
        id=updated.id,
        email=updated.email,
        name=updated.name,
        role=updated.role.value,
        created_at=updated.created_at,
    )
