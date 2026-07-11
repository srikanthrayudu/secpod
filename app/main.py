from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, Base
from app.api.api_v1 import api_router
from app.api.views import auth_views, dashboard_views, ai_views, qa_views
from app.utils.logger import logger
from app.services.ai import AIService
import app.models
import os

from app.core.seeder import auto_seed_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing database schemas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas created successfully.")
    
    # Automate database seeding
    try:
        await auto_seed_db()
    except Exception as e:
        logger.error(f"Failed to auto-seed database: {e}")
        
    yield
    # Shutdown actions
    logger.info("Shutting down application server.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SecPod QA Test Management & Automation Platform — plan, run, and track manual and automated tests.",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files folder (ensure directory exists)
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
with open("app/static/css/style.css", "a") as f:
    pass
with open("app/static/js/main.js", "a") as f:
    pass

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Global exception handler for Auth/View redirection
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    is_auth_error = exc.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    # HTMX partial requests can't follow a server redirect — send HX-Redirect header instead (§23)
    if is_auth_error and request.headers.get("hx-request"):
        logger.info("Sending HX-Redirect to unauthenticated HTMX request.")
        response = JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        response.headers["HX-Redirect"] = "/login"
        response.delete_cookie("access_token")
        return response

    # Full-page browser request — redirect to login
    accept_header = request.headers.get("accept", "")
    if is_auth_error and "text/html" in accept_header:
        logger.info("Redirecting unauthenticated HTML request to login page.")
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("access_token")
        return response

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Root View Redirect
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/dashboard")

# Health Check API
@app.get("/health", tags=["monitoring"])
async def health_check():
    db_status = "ok"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Health check database probe failed: {e}")
        db_status = "error"

    redis_status = "skipped"
    if settings.REDIS_URL:
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            await client.ping()
            await client.aclose()
            redis_status = "ok"
        except Exception as e:
            logger.warning(f"Health check redis probe failed: {e}")
            redis_status = "error"

    ai_status = "ok"
    try:
        AIService()
    except Exception as e:
        logger.warning(f"Health check AI provider probe failed: {e}")
        ai_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return {
        "status": overall,
        "db": db_status,
        "redis": redis_status,
        "ai_provider": ai_status,
        "project": settings.PROJECT_NAME,
    }

# Include API v1 Router
app.include_router(api_router, prefix="/api/v1")

# Include Jinja2 HTML Page Views
app.include_router(auth_views.router)
app.include_router(dashboard_views.router)
app.include_router(ai_views.router)
app.include_router(qa_views.router)
