from datetime import date

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.defect import Defect
from app.models.release import Release
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.user import User
from app.utils.logger import logger

DEFAULT_PASSWORD = "password123"

DEFAULT_USERS: list[dict] = [
    {
        "email": "admin@qualityhub.local",
        "full_name": "Alex Administrator",
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "bio": "Platform administrator for SecPod QA.",
        "company": "SecPod",
        "location": "Bangalore, IN",
    },
    {
        "email": "lead@qualityhub.local",
        "full_name": "Priya QA Lead",
        "role": "qa_lead",
        "is_active": True,
        "is_verified": True,
        "bio": "QA Lead overseeing release readiness and defect triage.",
        "company": "SecPod",
        "location": "Bangalore, IN",
    },
    {
        "email": "engineer@qualityhub.local",
        "full_name": "Sam Engineer",
        "role": "qa_engineer",
        "is_active": True,
        "is_verified": True,
        "bio": "QA Engineer executing manual and automated test suites.",
        "company": "SecPod",
        "location": "Hyderabad, IN",
    },
    {
        "email": "inactive@qualityhub.local",
        "full_name": "Deactivated User",
        "role": "qa_engineer",
        "is_active": False,
        "is_verified": True,
        "bio": "This account should not be able to log in.",
        "company": "SecPod",
        "location": "Chennai, IN",
    },
]

SEED_EMAILS = {user["email"] for user in DEFAULT_USERS}


async def _seed_default_users(db) -> int:
    """Ensure default QualityHub accounts exist. Returns number of users created."""
    created = 0
    hashed_password = get_password_hash(DEFAULT_PASSWORD)

    for user_data in DEFAULT_USERS:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing = result.scalars().first()
        if existing:
            if settings.ENV == "development" and user_data["email"] in SEED_EMAILS:
                existing.hashed_password = hashed_password
                existing.role = user_data["role"]
                existing.is_active = user_data["is_active"]
                existing.is_verified = user_data["is_verified"]
            continue

        db.add(User(hashed_password=hashed_password, **user_data))
        created += 1

    return created


async def _seed_demo_qa_data(db) -> bool:
    """Populate demo releases, test cases, runs, and defects when QA tables are empty."""
    result = await db.execute(select(TestCase).limit(1))
    if result.scalars().first():
        logger.info("QA data already present. Skipping demo QA seed.")
        return False

    admin = (
        await db.execute(select(User).where(User.email == "admin@qualityhub.local"))
    ).scalars().first()
    engineer = (
        await db.execute(select(User).where(User.email == "engineer@qualityhub.local"))
    ).scalars().first()
    if not admin or not engineer:
        logger.warning("Default users missing; cannot seed demo QA data.")
        return False

    release = Release(
        name="v2.4.0",
        target_date=date(2026, 7, 25),
        status="in_progress",
    )
    db.add(release)
    await db.flush()

    test_cases = [
        TestCase(
            title="User login with valid credentials",
            module="Authentication",
            priority="critical",
            steps=[
                "Navigate to /login",
                "Enter valid email and password",
                "Click Sign In",
            ],
            expected_result="User is redirected to the dashboard.",
            tags=["smoke", "auth"],
            created_by=engineer.id,
        ),
        TestCase(
            title="Create a new test case",
            module="Test Management",
            priority="high",
            steps=[
                "Log in as QA Engineer",
                "Open Test Cases and click New",
                "Fill in title, module, steps, and expected result",
                "Save the test case",
            ],
            expected_result="The new test case appears in the list.",
            tags=["regression", "crud"],
            created_by=engineer.id,
        ),
        TestCase(
            title="Record a failed manual test run",
            module="Execution",
            priority="medium",
            steps=[
                "Open a test case",
                "Click Execute",
                "Mark the run as Failed and add notes",
            ],
            expected_result="A failed run is saved and can be linked to a defect.",
            tags=["manual", "execution"],
            created_by=engineer.id,
        ),
    ]
    db.add_all(test_cases)
    await db.flush()

    runs = [
        TestRun(
            test_case_id=test_cases[0].id,
            release_id=release.id,
            status="passed",
            source="manual",
            duration_ms=4200,
            executed_by=engineer.id,
        ),
        TestRun(
            test_case_id=test_cases[1].id,
            release_id=release.id,
            status="passed",
            source="manual",
            duration_ms=8900,
            executed_by=engineer.id,
        ),
        TestRun(
            test_case_id=test_cases[2].id,
            release_id=release.id,
            status="failed",
            source="manual",
            duration_ms=6100,
            logs="Defect dialog did not open after marking run as failed.",
            executed_by=engineer.id,
        ),
    ]
    db.add_all(runs)
    await db.flush()

    db.add(
        Defect(
            title="Defect link missing on failed manual run",
            description="When a manual run is marked failed, the UI does not prompt to create or link a defect.",
            severity="high",
            status="open",
            test_run_id=runs[2].id,
        )
    )
    logger.info("Demo QA data seeded (release v2.4.0, 3 test cases, 3 runs, 1 defect).")
    return True


async def auto_seed_db():
    logger.info("Checking database for seeding...")
    async with SessionLocal() as db:
        users_created = await _seed_default_users(db)
        if users_created:
            await db.flush()
        qa_seeded = await _seed_demo_qa_data(db)
        await db.commit()

        if users_created:
            logger.info("Created %s default QualityHub account(s).", users_created)
        else:
            logger.info("Default QualityHub accounts are present.")

        if not qa_seeded and users_created == 0:
            logger.info("Database seeding check complete — no changes needed.")
