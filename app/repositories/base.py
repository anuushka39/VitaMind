"""
Generic repository base.

Why this exists: eight entities need identical CRUD plumbing (get by id,
list, create, update, delete). Writing that eight times would be exactly
the "duplicated logic" the architecture rules forbid. Entity-specific
repositories inherit this and add ONLY their genuinely custom queries
(e.g. "find logs for a user within a date range") — never override the
basic CRUD methods below.

This is the only layer allowed to touch `db.query`/`db.execute` directly.
Services never import sqlalchemy.
"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def get(self, id: int) -> ModelType | None:
        return self.db.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()
