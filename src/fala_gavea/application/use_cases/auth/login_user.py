from __future__ import annotations

from datetime import timedelta

from fala_gavea import config
from fala_gavea.domain.exceptions import InvalidCredentialsError
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.jwt_service import JWTService
from fala_gavea.infrastructure.auth.password_service import PasswordService


class LoginUser:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_service: PasswordService,
        jwt_service: JWTService,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._jwt_service = jwt_service

    def execute(self, email: str, password: str) -> str:
        user = self._user_repo.find_by_email(email)
        if user is None:
            raise InvalidCredentialsError()
        if not self._password_service.verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        return self._jwt_service.create_access_token(
            user.id,
            user.role.value,
            timedelta(hours=config.JWT_EXPIRY_HOURS),
        )
