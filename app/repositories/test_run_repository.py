import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.test_run import TestRun
from app.repositories.base import BaseRepository

class TestRunRepository(BaseRepository[TestRun]):
    def __init__(self, db: AsyncSession):
        super().__init__(TestRun, db)

    async def get_by_release(self, release_id: str | uuid.UUID) -> list[TestRun]:
        uid = uuid.UUID(release_id) if isinstance(release_id, str) else release_id
        result = await self.db.execute(select(TestRun).filter(TestRun.release_id == uid))
        return list(result.scalars().all())

    async def get_by_test_case(self, test_case_id: str | uuid.UUID) -> list[TestRun]:
        uid = uuid.UUID(test_case_id) if isinstance(test_case_id, str) else test_case_id
        result = await self.db.execute(select(TestRun).filter(TestRun.test_case_id == uid).order_by(TestRun.created_at.desc()))
        return list(result.scalars().all())
