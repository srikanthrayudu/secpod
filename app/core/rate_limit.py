from fastapi import HTTPException, status
from app.core.config import settings
from app.utils.logger import logger

async def check_rate_limit(key: str, *, max_attempts: int = 10, window_seconds: int = 300) -> None:
    """Redis-backed rate limiter. Fails open when Redis is unavailable."""
    if not settings.REDIS_URL:
        return

    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        redis_key = f"rate_limit:{key}"
        count = await client.incr(redis_key)
        if count == 1:
            await client.expire(redis_key, window_seconds)
        await client.aclose()
        if count > max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Rate limit check skipped (Redis unavailable): {exc}")
