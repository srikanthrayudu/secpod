from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.utils.logger import logger

async def auto_seed_db():
    logger.info("Checking database for seeding...")
    async with SessionLocal() as db:
        res = await db.execute(select(User).limit(1))
        if res.scalars().first():
            logger.info("Database already contains user data. Skipping auto-seed.")
            return

        logger.info("No user data found. Starting automatic database seeding...")
        users = [
            User(
                email="admin@qualityhub.local",
                hashed_password=get_password_hash("password123"),
                full_name="Alex Administrator",
                role="admin",
                is_active=True,
                is_verified=True,
                bio="Platform administrator for SecPod QA.",
                company="SecPod",
                location="Bangalore, IN",
            ),
            User(
                email="lead@qualityhub.local",
                hashed_password=get_password_hash("password123"),
                full_name="Priya QA Lead",
                role="qa_lead",
                is_active=True,
                is_verified=True,
                bio="QA Lead overseeing release readiness and defect triage.",
                company="SecPod",
                location="Bangalore, IN",
            ),
            User(
                email="engineer@qualityhub.local",
                hashed_password=get_password_hash("password123"),
                full_name="Sam Engineer",
                role="qa_engineer",
                is_active=True,
                is_verified=True,
                bio="QA Engineer executing manual and automated test suites.",
                company="SecPod",
                location="Hyderabad, IN",
            ),
            User(
                email="inactive@qualityhub.local",
                hashed_password=get_password_hash("password123"),
                full_name="Deactivated User",
                role="qa_engineer",
                is_active=False,
                is_verified=True,
                bio="This account should not be able to log in.",
                company="SecPod",
                location="Chennai, IN",
            ),
        ]

        db.add_all(users)
        await db.commit()
        logger.info("Database auto-seeded successfully with default QA accounts.")
