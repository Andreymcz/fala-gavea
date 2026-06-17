from __future__ import annotations

from fala_gavea.domain.entities.user import User
from fala_gavea.domain.exceptions import UserAlreadyExistsError, InvalidInputError
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.auth.password_service import PasswordService


class RegisterUser:
    def __init__(self, user_repo: IUserRepository, password_service: PasswordService) -> None:
        self._user_repo = user_repo
        self._password_service = password_service

    def execute(self, email: str, password: str, name: str) -> User:
        name = name.strip()
        if len(name) < 2 or len(name) > 100:
            raise InvalidInputError("name must be 2-100 characters")
        existing = self._user_repo.find_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsError(f"Email already registered: {email}")
        hashed = self._password_service.hash_password(password)
        return self._user_repo.save(User.create(email, hashed, name))
