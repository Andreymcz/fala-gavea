from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.user import User, UserRole
from fala_gavea.domain.repositories.user_repository import IUserRepository
from fala_gavea.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> User:
        model = self._session.get(UserModel, user.id)
        if model is None:
            model = self._to_model(user)
            self._session.add(model)
        else:
            model.email = user.email
            model.password_hash = user.password_hash
            model.name = user.name
            model.role = user.role.value
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, id: str) -> User | None:
        model = self._session.get(UserModel, id)
        return self._to_entity(model) if model else None

    def find_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        model = self._session.scalars(stmt).first()
        return self._to_entity(model) if model else None

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            name=user.name,
            role=user.role.value,
            created_at=user.created_at,
        )

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            name=model.name,
            role=UserRole(model.role),
            created_at=model.created_at,
        )
