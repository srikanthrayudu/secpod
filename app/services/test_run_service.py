import uuid
import os
from typing import Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.test_run import TestRun
from app.models.test_case import TestCase
from app.models.release import Release
from app.models.defect import Defect
from app.models.evidence import Evidence
from app.repositories.test_run_repository import TestRunRepository
from app.repositories.evidence_repository import EvidenceRepository
from app.schemas.test_run import TestRunCreate, TestRunUpdate

def _schedule_coverage_recompute() -> None:
    try:
        from app.background.worker import recompute_coverage
        recompute_coverage.delay()
    except Exception:
        pass

class TestRunService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TestRunRepository(db)
        self.evidence_repo = EvidenceRepository(db)

    async def get_test_run(self, id: uuid.UUID | str) -> TestRun | None:
        return await self.repo.get(id)

    async def get_test_runs(
        self,
        *,
        release_id: uuid.UUID | str | None = None,
        status: str | None = None,
        source: str | None = None,
        module: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[TestRun]:
        query = select(TestRun)
        
        if release_id:
            uid = uuid.UUID(release_id) if isinstance(release_id, str) else release_id
            query = query.filter(TestRun.release_id == uid)
            
        if status:
            query = query.filter(TestRun.status == status)
            
        if source:
            query = query.filter(TestRun.source == source)
            
        if module:
            query = query.join(TestCase).filter(TestCase.module == module)
            
        query = query.offset(skip).limit(limit)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_test_run(self, obj_in: TestRunCreate) -> TestRun:
        test_case = await self.db.get(TestCase, obj_in.test_case_id)
        if not test_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.")

        release = await self.db.get(Release, obj_in.release_id)
        if not release:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found.")

        run_data = obj_in.model_dump()
        db_run = await self.repo.create(run_data)

        if db_run.status == "failed":
            defect_title = f"Defect: Test Case '{test_case.title}' Failed"
            severity = test_case.priority if test_case.priority in ["low", "medium", "high", "critical"] else "medium"
            defect_desc = (
                f"Test run {db_run.id} failed.\n"
                f"Source: {db_run.source}\n"
                f"Duration: {db_run.duration_ms} ms\n"
                f"Expected Result: {test_case.expected_result}\n\n"
                f"Logs:\n{db_run.logs or 'No logs provided.'}"
            )
            defect_data = {
                "title": defect_title,
                "description": defect_desc,
                "severity": severity,
                "status": "open",
                "test_run_id": db_run.id
            }
            db_defect = Defect(**defect_data)
            self.db.add(db_defect)
            await self.db.commit()

        _schedule_coverage_recompute()
        return db_run

    async def get_evidence_for_run(self, test_run_id: uuid.UUID) -> list[Evidence]:
        return await self.evidence_repo.get_by_test_run(test_run_id)

    async def attach_evidence(self, test_run_id: uuid.UUID, file: UploadFile) -> Evidence:
        test_run = await self.repo.get(test_run_id)
        if not test_run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found.")

        max_size = 5 * 1024 * 1024
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File too large. Max 5MB.")

        allowed_types = ["image/png", "image/jpeg", "image/gif", "text/plain", "text/log", "application/json"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"File type {file.content_type} not allowed.")

        upload_dir = "uploads/evidence"
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        evidence_data = {
            "test_run_id": test_run_id,
            "file_path": file_path,
            "file_type": file.content_type
        }
        return await self.evidence_repo.create(evidence_data)
