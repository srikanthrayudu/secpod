import uuid
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.release import Release
from app.models.test_run import TestRun
from app.models.test_case import TestCase
from app.models.defect import Defect
from app.repositories.release_repository import ReleaseRepository
from app.schemas.release import ReleaseCreate, ReleaseUpdate

class ReleaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReleaseRepository(db)

    async def get_release(self, id: uuid.UUID | str) -> Release | None:
        return await self.repo.get(id)

    async def get_releases(self, skip: int = 0, limit: int = 100) -> list[Release]:
        return await self.repo.get_multi(skip=skip, limit=limit)

    async def create_release(self, obj_in: ReleaseCreate) -> Release:
        existing = await self.repo.get_by_name(obj_in.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Release name already exists.")
        data = obj_in.model_dump()
        return await self.repo.create(data)

    async def get_readiness(self, id: uuid.UUID | str) -> dict[str, Any]:
        uid = uuid.UUID(id) if isinstance(id, str) else id
        release = await self.get_release(uid)
        if not release:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found.")

        # 1. Total active test cases
        tc_res = await self.db.execute(select(func.count(TestCase.id)).filter(TestCase.archived == False))
        total_test_cases = tc_res.scalar() or 0

        # 2. Unique test cases run in this release
        tr_res = await self.db.execute(
            select(func.count(func.distinct(TestRun.test_case_id)))
            .filter(TestRun.release_id == uid)
        )
        run_test_cases = tr_res.scalar() or 0

        # 3. Pass rate: passed runs / total runs
        runs_total_res = await self.db.execute(select(func.count(TestRun.id)).filter(TestRun.release_id == uid))
        total_runs = runs_total_res.scalar() or 0

        runs_passed_res = await self.db.execute(
            select(func.count(TestRun.id)).filter(TestRun.release_id == uid, TestRun.status == "passed")
        )
        passed_runs = runs_passed_res.scalar() or 0

        pass_rate = (passed_runs / total_runs * 100.0) if total_runs > 0 else 0.0
        coverage_pct = (run_test_cases / total_test_cases * 100.0) if total_test_cases > 0 else 0.0

        # 4. Count of open defects in this release
        defects_res = await self.db.execute(
            select(func.count(Defect.id))
            .join(TestRun, Defect.test_run_id == TestRun.id)
            .filter(TestRun.release_id == uid, Defect.status.in_(["open", "triaged"]))
        )
        open_defects = defects_res.scalar() or 0

        critical_res = await self.db.execute(
            select(Defect)
            .join(TestRun, Defect.test_run_id == TestRun.id)
            .filter(
                TestRun.release_id == uid,
                Defect.severity == "critical",
                Defect.status.in_(["open", "triaged"]),
            )
        )
        critical_blockers = list(critical_res.scalars().all())

        return {
            "release_id": uid,
            "release_name": release.name,
            "total_test_cases": total_test_cases,
            "executed_test_cases": run_test_cases,
            "coverage_percentage": round(coverage_pct, 2),
            "pass_rate_percentage": round(pass_rate, 2),
            "open_defects_count": open_defects,
            "critical_blockers_count": len(critical_blockers),
            "has_release_blockers": len(critical_blockers) > 0,
            "critical_blockers": [
                {"id": str(d.id), "title": d.title, "severity": d.severity, "status": d.status}
                for d in critical_blockers
            ],
            "status": release.status
        }
