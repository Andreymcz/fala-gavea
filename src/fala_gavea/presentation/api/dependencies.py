from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import InvalidCredentialsError
from fala_gavea.domain.repositories.report_repository import IReportRepository
from fala_gavea.domain.repositories.report_type_repository import IReportTypeRepository
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.jwt_service import JWTService
from fala_gavea.infrastructure.auth.password_service import PasswordService
from fala_gavea.infrastructure.database.session import SessionLocal
from fala_gavea.infrastructure.repositories.sqlalchemy_report_repository import SQLAlchemyReportRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_report_type_repository import SQLAlchemyReportTypeRepository
from fala_gavea.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_repo(db: Session = Depends(get_db)) -> IUserRepository:
    return SQLAlchemyUserRepository(db)


def get_report_repo(db: Session = Depends(get_db)) -> IReportRepository:
    return SQLAlchemyReportRepository(db)


def get_report_type_repo(db: Session = Depends(get_db)) -> IReportTypeRepository:
    return SQLAlchemyReportTypeRepository(db)


def get_password_service() -> PasswordService:
    return PasswordService()


def get_jwt_service() -> JWTService:
    return JWTService()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: IUserRepository = Depends(get_user_repo),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> User:
    try:
        payload = jwt_service.decode_token(token)
        user_id: str = payload.get("sub", "")
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_repo.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: str):
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    return _check
