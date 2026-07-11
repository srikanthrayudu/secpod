import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.evidence import Evidence
from app.repositories.base import BaseRepository

class EvidenceRepository(BaseRepository[Evidence]):
    def __init__(self, db: AsyncSession):
        super().__init__(Evidence, db)

    async def get_by_test_run(self, test_run_id: str | uuid.UUID) -> list[Evidence]:
        uid = uuid.UUID(test_run_id) if isinstance(test_run_id, str) else test_run_id
        result = await self.db.execute(select(Evidence).filter(Evidence.test_run_id == uid))
        return list(result.scalars().all())
