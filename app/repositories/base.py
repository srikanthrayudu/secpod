from typing import Any, Generic, TypeVar
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> ModelType | None:
        import uuid
        if isinstance(id, str):
            try:
                id = uuid.UUID(id)
            except ValueError:
                pass
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def remove(self, id: Any) -> ModelType | None:
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj
