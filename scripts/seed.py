import asyncio
from app.core.database import engine, Base
from app.core.seeder import auto_seed_db

if __name__ == "__main__":
    # Ensure tables are built
    async def main():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await auto_seed_db()
    asyncio.run(main())
