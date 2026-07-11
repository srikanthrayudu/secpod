from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.release import Release
from app.repositories.base import BaseRepository

class ReleaseRepository(BaseRepository[Release]):
    def __init__(self, db: AsyncSession):
        super().__init__(Release, db)

    async def get_by_name(self, name: str) -> Release | None:
        result = await self.db.execute(select(Release).filter(Release.name == name))
        return result.scalars().first()
