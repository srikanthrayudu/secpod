from fastapi import APIRouter
from app.api.endpoints import auth, users, ai, test_cases, test_runs, defects, releases

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["test-cases"])
api_router.include_router(test_runs.router, prefix="/test-runs", tags=["test-runs"])
api_router.include_router(defects.router, prefix="/defects", tags=["defects"])
api_router.include_router(releases.router, prefix="/releases", tags=["releases"])
