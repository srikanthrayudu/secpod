from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.services.ai import AIService
from app.services.release_service import ReleaseService
from app.utils.logger import logger
import uuid

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None


@router.get("/dashboard/ai", response_class=HTMLResponse)
async def ai_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    release_service = ReleaseService(db)
    releases = await release_service.get_releases(limit=50)
    return templates.TemplateResponse(
        request=request,
        name="ai/playground.html",
        context={"user": current_user, "active_tab": "ai", "releases": releases},
    )


@router.post("/dashboard/ai/draft", response_class=HTMLResponse)
async def ai_draft_test_case(
    request: Request,
    requirement_text: str = Form(...),
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_active_user),
):
    try:
        draft = await ai_service.draft_test_case(requirement_text)
    except Exception as e:
        logger.error(f"AI draft failed: {e}")
        draft = None
        error = str(e)
    else:
        error = None

    return templates.TemplateResponse(
        request=request,
        name="ai/draft_result.html",
        context={
            "draft": draft,
            "requirement_text": requirement_text,
            "error": error,
        },
    )


@router.post("/dashboard/ai/summarize", response_class=HTMLResponse)
async def ai_summarize_failures(
    request: Request,
    release_id: uuid.UUID = Form(...),
    limit: int = Form(50),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(deps.get_ai_service),
    current_user: User = Depends(deps.get_current_active_user),
):
    if current_user.role not in ["qa_lead", "admin"]:
        return HTMLResponse(
            content='<p class="text-sm text-rose-400">Only QA Leads and Admins can run failure summarization.</p>',
            status_code=403,
        )

    from app.services.test_run_service import TestRunService

    release_service = ReleaseService(db)
    release = await release_service.get_release(release_id)
    if not release:
        return HTMLResponse(
            content='<p class="text-sm text-rose-400">Release not found.</p>',
            status_code=404,
        )

    run_service = TestRunService(db)
    failed_runs = await run_service.get_test_runs(release_id=release_id, status="failed", limit=limit)
    logs = [run.logs for run in failed_runs if run.logs]

    try:
        summary = await ai_service.summarize_failures(logs)
    except Exception as e:
        logger.error(f"AI summarize failed: {e}")
        return HTMLResponse(
            content=f'<p class="text-sm text-rose-400">Failed to generate summary: {e}</p>',
            status_code=503,
        )

    return templates.TemplateResponse(
        request=request,
        name="ai/summary_result.html",
        context={
            "summary": summary,
            "release": release,
            "failed_count": len(failed_runs),
        },
    )
