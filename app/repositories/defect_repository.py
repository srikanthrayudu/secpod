from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.defect import Defect
from app.repositories.base import BaseRepository

class DefectRepository(BaseRepository[Defect]):
    def __init__(self, db: AsyncSession):
        super().__init__(Defect, db)

    async def get_open_defects(self) -> list[Defect]:
        result = await self.db.execute(select(Defect).filter(Defect.status == "open"))
        return list(result.scalars().all())
