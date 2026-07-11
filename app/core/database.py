from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Apply SQLite-specific parameters if needed
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG and not settings.DATABASE_URL.startswith("sqlite"),
    future=True,
)

# Async Session Factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Declarative Base Class
class Base(DeclarativeBase):
    pass

# Dependency to yield AsyncSession in routes/handlers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
