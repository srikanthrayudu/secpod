import uuid
from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.test_case import TestCase
from app.repositories.test_case_repository import TestCaseRepository
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate

class TestCaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TestCaseRepository(db)

    async def get_test_case(self, id: uuid.UUID | str) -> TestCase | None:
        return await self.repo.get(id)

    async def get_test_cases(
        self,
        *,
        module: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> list[TestCase]:
        query = select(TestCase)
        
        if not include_archived:
            query = query.filter(TestCase.archived == False)
            
        if module:
            query = query.filter(TestCase.module == module)
            
        if priority:
            query = query.filter(TestCase.priority == priority)
            
        if search:
            search_filter = or_(
                TestCase.title.ilike(f"%{search}%"),
                TestCase.expected_result.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        query = query.offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_test_case(self, obj_in: TestCaseCreate, user_id: uuid.UUID) -> TestCase:
        data = obj_in.model_dump()
        data["created_by"] = user_id
        return await self.repo.create(data)

    async def update_test_case(self, db_obj: TestCase, obj_in: TestCaseUpdate) -> TestCase:
        data = obj_in.model_dump(exclude_unset=True)
        return await self.repo.update(db_obj, data)

    async def delete_test_case(self, id: uuid.UUID | str) -> TestCase | None:
        # We archive rather than hard delete by default, per column requirements
        db_obj = await self.get_test_case(id)
        if db_obj:
            db_obj.archived = True
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
        return db_obj
