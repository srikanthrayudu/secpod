import json
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.defect import Defect
from app.models.release import Release
from app.models.test_case import TestCase
from app.models.test_run import TestRun

CACHE_KEY = "coverage:aggregate"
CACHE_TTL_SECONDS = 300


class CoverageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _redis_get(self, key: str) -> dict[str, Any] | None:
        if not settings.REDIS_URL:
            return None
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            raw = await client.get(key)
            await client.aclose()
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def _redis_set(self, key: str, payload: dict[str, Any]) -> None:
        if not settings.REDIS_URL:
            return
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            await client.set(key, json.dumps(payload, default=str), ex=CACHE_TTL_SECONDS)
            await client.aclose()
        except Exception:
            pass

    async def compute_coverage(
        self,
        *,
        release_id: uuid.UUID | str | None = None,
        module: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict[str, Any]:
        release_uid = uuid.UUID(release_id) if isinstance(release_id, str) else release_id

        tc_query = select(TestCase).filter(TestCase.archived == False)
        if module:
            tc_query = tc_query.filter(TestCase.module == module)
        tc_res = await self.db.execute(tc_query)
        test_cases = list(tc_res.scalars().all())
        total_cases = len(test_cases)
        case_ids = {tc.id for tc in test_cases}

        run_query = select(TestRun)
        if release_uid:
            run_query = run_query.filter(TestRun.release_id == release_uid)
        if module:
            run_query = run_query.join(TestCase).filter(TestCase.module == module)
        if date_from:
            run_query = run_query.filter(TestRun.created_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc))
        if date_to:
            run_query = run_query.filter(
                TestRun.created_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc)
            )

        run_res = await self.db.execute(run_query)
        runs = list(run_res.scalars().all())
        if case_ids:
            runs = [r for r in runs if r.test_case_id in case_ids]

        executed_case_ids = {r.test_case_id for r in runs}
        passed = sum(1 for r in runs if r.status == "passed")
        failed = sum(1 for r in runs if r.status == "failed")
        total_runs = len(runs)
        manual_runs = sum(1 for r in runs if r.source == "manual")
        automated_runs = sum(1 for r in runs if r.source == "automated")

        coverage_pct = round(len(executed_case_ids) / total_cases * 100, 1) if total_cases else 0.0
        pass_rate = round(passed / total_runs * 100, 1) if total_runs else 0.0

        by_module: dict[str, dict[str, Any]] = {}
        for tc in test_cases:
            mod = tc.module
            if mod not in by_module:
                by_module[mod] = {"module": mod, "total": 0, "executed": 0, "passed": 0, "failed": 0, "runs": 0}
            by_module[mod]["total"] += 1
            if tc.id in executed_case_ids:
                by_module[mod]["executed"] += 1

        for run in runs:
            tc = next((t for t in test_cases if t.id == run.test_case_id), None)
            if not tc:
                continue
            by_module[tc.module]["runs"] += 1
            if run.status == "passed":
                by_module[tc.module]["passed"] += 1
            elif run.status == "failed":
                by_module[tc.module]["failed"] += 1

        module_rows = []
        for row in sorted(by_module.values(), key=lambda x: x["module"]):
            row["coverage_pct"] = round(row["executed"] / row["total"] * 100, 1) if row["total"] else 0.0
            row["pass_rate_pct"] = round(row["passed"] / row["runs"] * 100, 1) if row["runs"] else 0.0
            module_rows.append(row)

        trend: dict[str, dict[str, int]] = {}
        for run in runs:
            day = run.created_at.date().isoformat()
            if day not in trend:
                trend[day] = {"date": day, "passed": 0, "failed": 0, "total": 0}
            trend[day]["total"] += 1
            if run.status == "passed":
                trend[day]["passed"] += 1
            elif run.status == "failed":
                trend[day]["failed"] += 1

        trend_rows = []
        for day in sorted(trend.keys()):
            row = trend[day]
            row["pass_rate_pct"] = round(row["passed"] / row["total"] * 100, 1) if row["total"] else 0.0
            trend_rows.append(row)

        open_defects = 0
        critical_defects = 0
        defect_query = select(Defect)
        if release_uid:
            defect_query = defect_query.join(TestRun, Defect.test_run_id == TestRun.id).filter(
                TestRun.release_id == release_uid
            )
        defect_res = await self.db.execute(defect_query)
        for defect in defect_res.scalars().all():
            if defect.status in {"open", "triaged"}:
                open_defects += 1
                if defect.severity == "critical":
                    critical_defects += 1

        return {
            "filters": {
                "release_id": str(release_uid) if release_uid else None,
                "module": module,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "summary": {
                "total_test_cases": total_cases,
                "executed_test_cases": len(executed_case_ids),
                "coverage_percentage": coverage_pct,
                "pass_rate_percentage": pass_rate,
                "total_runs": total_runs,
                "passed_runs": passed,
                "failed_runs": failed,
                "manual_runs": manual_runs,
                "automated_runs": automated_runs,
                "open_defects": open_defects,
                "critical_defects": critical_defects,
            },
            "by_module": module_rows,
            "trend": trend_rows[-14:],
        }

    async def get_coverage(
        self,
        *,
        release_id: uuid.UUID | str | None = None,
        module: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        cache_key = f"{CACHE_KEY}:{release_id or 'all'}:{module or 'all'}:{date_from or 'all'}:{date_to or 'all'}"
        if use_cache:
            cached = await self._redis_get(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached

        result = await self.compute_coverage(
            release_id=release_id,
            module=module,
            date_from=date_from,
            date_to=date_to,
        )
        result["from_cache"] = False
        await self._redis_set(cache_key, result)
        return result

    async def recompute_all_cache(self) -> int:
        """Precompute coverage for all releases and the global view."""
        releases = (await self.db.execute(select(Release))).scalars().all()
        keys_written = 0

        global_data = await self.compute_coverage()
        await self._redis_set(f"{CACHE_KEY}:all:all:all:all", global_data)
        keys_written += 1

        for release in releases:
            data = await self.compute_coverage(release_id=release.id)
            await self._redis_set(f"{CACHE_KEY}:{release.id}:all:all:all", data)
            keys_written += 1

        return keys_written

    async def get_module_drilldown(self, module: str, release_id: uuid.UUID | str | None = None) -> dict[str, Any]:
        return await self.get_coverage(release_id=release_id, module=module)
