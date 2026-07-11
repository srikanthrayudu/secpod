from celery import Celery
from app.core.config import settings
from app.utils.logger import logger

celery_app = Celery(
    "background_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="tasks.recompute_coverage")
def recompute_coverage() -> str:
    """Precompute coverage aggregates and store them in Redis."""
    import asyncio
    from app.core.database import SessionLocal
    from app.services.coverage_service import CoverageService

    async def _run() -> int:
        async with SessionLocal() as db:
            service = CoverageService(db)
            return await service.recompute_all_cache()

    count = asyncio.run(_run())
    logger.info(f"[Celery Task] Recomputed coverage cache for {count} release views.")
    return f"Coverage cache updated ({count} keys)"


@celery_app.task(name="tasks.send_welcome_email")
def send_welcome_email(email: str, name: str) -> str:
    logger.info(f"[Celery Task] Sending welcome email to {name} <{email}>")
    return f"Welcome email sent to {email}"
