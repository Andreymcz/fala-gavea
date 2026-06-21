from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fala_gavea.domain.entities.saved_filter import SavedFilter
from fala_gavea.domain.repositories.saved_filter_repository import ISavedFilterRepository
from fala_gavea.infrastructure.database.models import SavedFilterModel


class SQLAlchemySavedFilterRepository(ISavedFilterRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, sf: SavedFilter) -> SavedFilter:
        model = SavedFilterModel(
            id=sf.id,
            owner_id=sf.owner_id,
            name=sf.name,
            body=sf.body,
            schema_ver=sf.schema_ver,
            created_at=sf.created_at,
            updated_at=sf.updated_at,
        )
        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def find_by_id(self, id: str) -> SavedFilter | None:
        model = self._session.get(SavedFilterModel, id)
        return self._to_entity(model) if model else None

    def find_all_for_user(self, owner_id: str) -> list[SavedFilter]:
        stmt = (
            select(SavedFilterModel)
            .where(SavedFilterModel.owner_id == owner_id)
            .order_by(SavedFilterModel.created_at.desc())
        )
        return [self._to_entity(m) for m in self._session.scalars(stmt).all()]

    def update(self, sf: SavedFilter) -> SavedFilter:
        model = self._session.get(SavedFilterModel, sf.id)
        if model is None:
            raise ValueError(f"SavedFilter {sf.id!r} not found")
        model.name = sf.name
        model.body = sf.body
        model.schema_ver = sf.schema_ver
        model.updated_at = sf.updated_at
        self._session.commit()
        self._session.refresh(model)
        return self._to_entity(model)

    def delete(self, id: str) -> None:
        model = self._session.get(SavedFilterModel, id)
        if model is not None:
            self._session.delete(model)
            self._session.commit()

    def _to_entity(self, m: SavedFilterModel) -> SavedFilter:
        return SavedFilter(
            id=m.id,
            owner_id=m.owner_id,
            name=m.name,
            body=m.body,
            schema_ver=m.schema_ver,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
