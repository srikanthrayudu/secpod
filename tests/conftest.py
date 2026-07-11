import asyncio
import pytest
from collections.abc import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User

# Test Database Connection (SQLite in-memory with static pool for sharing across threads)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
async def init_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.close()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override database session dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    # Initialize Async Client using ASGI transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    hashed_pwd = get_password_hash("password123")
    user = User(
        email="testuser@example.com",
        hashed_password=hashed_pwd,
        full_name="Test User",
        role="qa_engineer",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_admin(db_session: AsyncSession) -> User:
    hashed_pwd = get_password_hash("password123")
    user = User(
        email="testadmin@example.com",
        hashed_password=hashed_pwd,
        full_name="Test Admin",
        role="admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
