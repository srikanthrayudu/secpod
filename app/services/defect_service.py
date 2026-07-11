import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.defect import Defect
from app.models.test_run import TestRun
from app.repositories.defect_repository import DefectRepository
from app.schemas.defect import DefectCreate, DefectUpdate

class DefectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DefectRepository(db)

    async def get_defect(self, id: uuid.UUID | str) -> Defect | None:
        return await self.repo.get(id)

    async def get_defects(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        release_id: uuid.UUID | str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Defect]:
        query = select(Defect)
        
        if status:
            query = query.filter(Defect.status == status)
            
        if severity:
            query = query.filter(Defect.severity == severity)
            
        if release_id:
            uid = uuid.UUID(release_id) if isinstance(release_id, str) else release_id
            query = query.join(TestRun, Defect.test_run_id == TestRun.id).filter(TestRun.release_id == uid)
            
        query = query.offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_defect(self, obj_in: DefectCreate) -> Defect:
        if obj_in.test_run_id:
            test_run = await self.db.get(TestRun, obj_in.test_run_id)
            if not test_run:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked test run not found.")
                
        data = obj_in.model_dump()
        return await self.repo.create(data)

    async def update_defect(self, db_obj: Defect, obj_in: DefectUpdate) -> Defect:
        data = obj_in.model_dump(exclude_unset=True)
        
        if "status" in data and data["status"] in ["fixed", "verified", "closed"]:
            data["resolved_at"] = datetime.now(timezone.utc)
        elif "status" in data and data["status"] in ["open", "triaged"]:
            data["resolved_at"] = None
            
        return await self.repo.update(db_obj, data)
