from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.test_case import TestCase
from app.repositories.base import BaseRepository

class TestCaseRepository(BaseRepository[TestCase]):
    def __init__(self, db: AsyncSession):
        super().__init__(TestCase, db)

    async def get_by_module(self, module: str, include_archived: bool = False) -> list[TestCase]:
        query = select(TestCase).filter(TestCase.module == module)
        if not include_archived:
            query = query.filter(TestCase.archived == False)
        result = await self.db.execute(query)
        return list(result.scalars().all())
