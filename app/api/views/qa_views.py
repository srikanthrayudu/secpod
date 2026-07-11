import uuid
from fastapi import APIRouter, Depends, Request, Form, Query, status, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.services.release_service import ReleaseService
from app.services.test_case_service import TestCaseService
from app.services.test_run_service import TestRunService
from app.services.defect_service import DefectService
from app.services.ai import AIService
from app.schemas.release import ReleaseCreate
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate
from app.schemas.test_run import TestRunCreate
from app.schemas.defect import DefectCreate, DefectUpdate
from app.utils.logger import logger

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None


# ---------------------------------------------------------------------------
# RELEASES
# ---------------------------------------------------------------------------

@router.get("/dashboard/releases", response_class=HTMLResponse)
async def releases_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = ReleaseService(db)
    releases = await service.get_releases(limit=50)
    return templates.TemplateResponse(
        request=request,
        name="qa/releases/index.html",
        context={"user": current_user, "releases": releases, "active_tab": "releases"},
    )


@router.get("/dashboard/releases/{release_id}", response_class=HTMLResponse)
async def release_detail(
    request: Request,
    release_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    release_service = ReleaseService(db)
    release = await release_service.get_release(release_id)
    if not release:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Release not found.", "active_tab": "releases"},
            status_code=404,
        )

    readiness = await release_service.get_readiness(release_id)

    run_service = TestRunService(db)
    recent_runs = await run_service.get_test_runs(release_id=release_id, limit=20)

    defect_service = DefectService(db)
    open_defects = await defect_service.get_defects(release_id=release_id, status="open", limit=10)

    return templates.TemplateResponse(
        request=request,
        name="qa/releases/detail.html",
        context={
            "user": current_user,
            "release": release,
            "readiness": readiness,
            "recent_runs": recent_runs,
            "open_defects": open_defects,
            "active_tab": "releases",
        },
    )


@router.post("/dashboard/releases", response_class=HTMLResponse)
async def create_release(
    request: Request,
    name: str = Form(...),
    target_date: str = Form(None),
    description: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    if current_user.role not in ["qa_lead", "admin"]:
        return templates.TemplateResponse(
            request=request,
            name="qa/releases/index.html",
            context={"user": current_user, "error": "Only QA Leads can create releases.", "active_tab": "releases"},
        )
    try:
        service = ReleaseService(db)
        obj_in = ReleaseCreate(name=name, target_date=target_date, description=description, status="planned")
        await service.create_release(obj_in)
        if request.headers.get("hx-request"):
            releases = await service.get_releases(limit=50)
            return templates.TemplateResponse(
                request=request,
                name="qa/releases/releases_table.html",
                context={"user": current_user, "releases": releases},
            )
        return RedirectResponse("/dashboard/releases", status_code=303)
    except Exception as e:
        logger.error(f"Create release error: {e}")
        service = ReleaseService(db)
        releases = await service.get_releases(limit=50)
        return templates.TemplateResponse(
            request=request,
            name="qa/releases/index.html",
            context={"user": current_user, "releases": releases, "error": str(e), "active_tab": "releases"},
        )


# ---------------------------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------------------------

@router.get("/dashboard/test-cases", response_class=HTMLResponse)
async def test_cases_index(
    request: Request,
    module: str = Query(None),
    priority: str = Query(None),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = TestCaseService(db)
    test_cases = await service.get_test_cases(module=module, priority=priority, search=search, limit=100)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request=request,
            name="qa/test_cases/table.html",
            context={"user": current_user, "test_cases": test_cases},
        )

    return templates.TemplateResponse(
        request=request,
        name="qa/test_cases/index.html",
        context={
            "user": current_user,
            "test_cases": test_cases,
            "active_tab": "test_cases",
            "module": module or "",
            "priority": priority or "",
            "search": search or "",
        },
    )


@router.get("/dashboard/test-cases/new", response_class=HTMLResponse)
async def new_test_case_form(
    request: Request,
    requirement: str = Query(None),
    current_user: User = Depends(deps.get_current_active_user),
    ai_service: AIService = Depends(deps.get_ai_service),
):
    draft = None
    if requirement:
        try:
            draft = await ai_service.draft_test_case(requirement)
        except Exception as e:
            logger.warning(f"AI draft failed: {e}")

    return templates.TemplateResponse(
        request=request,
        name="qa/test_cases/form.html",
        context={"user": current_user, "active_tab": "test_cases", "draft": draft, "requirement": requirement or ""},
    )


@router.post("/dashboard/test-cases", response_class=HTMLResponse)
async def create_test_case(
    request: Request,
    title: str = Form(...),
    module: str = Form(...),
    priority: str = Form("medium"),
    expected_result: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    try:
        form_data = await request.form()
        steps_raw = form_data.getlist("steps") or []
        tags_raw = form_data.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        service = TestCaseService(db)
        obj_in = TestCaseCreate(
            title=title,
            module=module,
            priority=priority,
            steps=steps_raw,
            expected_result=expected_result,
            tags=tags,
        )
        await service.create_test_case(obj_in, current_user.id)
        return RedirectResponse("/dashboard/test-cases", status_code=303)
    except Exception as e:
        logger.error(f"Create test case error: {e}")
        return templates.TemplateResponse(
            request=request,
            name="qa/test_cases/form.html",
            context={"user": current_user, "active_tab": "test_cases", "error": str(e)},
        )


@router.get("/dashboard/test-cases/{tc_id}", response_class=HTMLResponse)
async def test_case_detail(
    request: Request,
    tc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = TestCaseService(db)
    tc = await service.get_test_case(tc_id)
    if not tc:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Test case not found.", "active_tab": "test_cases"},
            status_code=404,
        )

    run_service = TestRunService(db)
    runs = await run_service.get_test_runs(limit=20)
    tc_runs = [r for r in runs if str(r.test_case_id) == str(tc_id)]

    return templates.TemplateResponse(
        request=request,
        name="qa/test_cases/detail.html",
        context={"user": current_user, "tc": tc, "runs": tc_runs, "active_tab": "test_cases"},
    )


@router.get("/dashboard/test-cases/{tc_id}/execute", response_class=HTMLResponse)
async def execute_test_case_form(
    request: Request,
    tc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    tc_service = TestCaseService(db)
    tc = await tc_service.get_test_case(tc_id)
    if not tc:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Test case not found.", "active_tab": "test_cases"},
            status_code=404,
        )

    release_service = ReleaseService(db)
    releases = await release_service.get_releases(limit=50)

    return templates.TemplateResponse(
        request=request,
        name="qa/test_cases/execute.html",
        context={"user": current_user, "tc": tc, "releases": releases, "active_tab": "test_cases"},
    )


@router.post("/dashboard/test-cases/{tc_id}/execute", response_class=HTMLResponse)
async def execute_test_case_submit(
    request: Request,
    tc_id: uuid.UUID,
    release_id: uuid.UUID = Form(...),
    status: str = Form(...),
    logs: str = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    tc_service = TestCaseService(db)
    tc = await tc_service.get_test_case(tc_id)
    if not tc:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Test case not found.", "active_tab": "test_cases"},
            status_code=404,
        )

    if status not in {"passed", "failed", "blocked", "skipped"}:
        release_service = ReleaseService(db)
        releases = await release_service.get_releases(limit=50)
        return templates.TemplateResponse(
            request=request,
            name="qa/test_cases/execute.html",
            context={
                "user": current_user,
                "tc": tc,
                "releases": releases,
                "active_tab": "test_cases",
                "error": "Invalid test run status.",
            },
        )

    try:
        run_service = TestRunService(db)
        obj_in = TestRunCreate(
            test_case_id=tc_id,
            release_id=release_id,
            status=status,
            source="manual",
            logs=logs,
            executed_by=current_user.id,
        )
        run = await run_service.create_test_run(obj_in)
        return RedirectResponse(f"/dashboard/test-runs/{run.id}", status_code=303)
    except Exception as e:
        logger.error(f"Manual test execution error: {e}")
        release_service = ReleaseService(db)
        releases = await release_service.get_releases(limit=50)
        return templates.TemplateResponse(
            request=request,
            name="qa/test_cases/execute.html",
            context={
                "user": current_user,
                "tc": tc,
                "releases": releases,
                "active_tab": "test_cases",
                "error": str(e),
            },
        )


# ---------------------------------------------------------------------------
# TEST RUNS
# ---------------------------------------------------------------------------

@router.get("/dashboard/test-runs", response_class=HTMLResponse)
async def test_runs_index(
    request: Request,
    release_id: str = Query(None),
    status_filter: str = Query(None, alias="status"),
    source: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    run_service = TestRunService(db)
    release_service = ReleaseService(db)

    runs = await run_service.get_test_runs(
        release_id=release_id,
        status=status_filter,
        source=source,
        limit=100,
    )
    releases = await release_service.get_releases(limit=50)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request=request,
            name="qa/test_runs/table.html",
            context={"user": current_user, "runs": runs},
        )

    return templates.TemplateResponse(
        request=request,
        name="qa/test_runs/index.html",
        context={
            "user": current_user,
            "runs": runs,
            "releases": releases,
            "active_tab": "test_runs",
            "release_id": release_id or "",
            "status_filter": status_filter or "",
            "source": source or "",
        },
    )


@router.get("/dashboard/test-runs/{run_id}", response_class=HTMLResponse)
async def test_run_detail(
    request: Request,
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = TestRunService(db)
    run = await service.get_test_run(run_id)
    if not run:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Test run not found.", "active_tab": "test_runs"},
            status_code=404,
        )

    defect_service = DefectService(db)
    all_defects = await defect_service.get_defects(limit=200)
    linked_defects = [d for d in all_defects if d.test_run_id and str(d.test_run_id) == str(run_id)]

    return templates.TemplateResponse(
        request=request,
        name="qa/test_runs/detail.html",
        context={"user": current_user, "run": run, "defects": linked_defects, "active_tab": "test_runs"},
    )


# ---------------------------------------------------------------------------
# DEFECTS
# ---------------------------------------------------------------------------

@router.get("/dashboard/defects", response_class=HTMLResponse)
async def defects_index(
    request: Request,
    status_filter: str = Query(None, alias="status"),
    severity: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = DefectService(db)
    defects = await service.get_defects(status=status_filter, severity=severity, limit=100)

    if request.headers.get("hx-request"):
        return templates.TemplateResponse(
            request=request,
            name="qa/defects/table.html",
            context={"user": current_user, "defects": defects},
        )

    return templates.TemplateResponse(
        request=request,
        name="qa/defects/index.html",
        context={
            "user": current_user,
            "defects": defects,
            "active_tab": "defects",
            "status_filter": status_filter or "",
            "severity": severity or "",
        },
    )


@router.get("/dashboard/defects/{defect_id}", response_class=HTMLResponse)
async def defect_detail(
    request: Request,
    defect_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    service = DefectService(db)
    defect = await service.get_defect(defect_id)
    if not defect:
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Defect not found.", "active_tab": "defects"},
            status_code=404,
        )
    return templates.TemplateResponse(
        request=request,
        name="qa/defects/detail.html",
        context={"user": current_user, "defect": defect, "active_tab": "defects"},
    )


@router.post("/dashboard/defects/{defect_id}/status", response_class=HTMLResponse)
async def update_defect_status(
    request: Request,
    defect_id: uuid.UUID,
    new_status: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    if current_user.role not in ["qa_lead", "admin"]:
        return HTMLResponse(
            content='<span class="text-rose-400 text-sm">Insufficient privileges.</span>',
            status_code=403,
        )
    service = DefectService(db)
    defect = await service.get_defect(defect_id)
    if not defect:
        return HTMLResponse(content="", status_code=404)

    updated = await service.update_defect(defect, DefectUpdate(status=new_status))

    badge_color = {
        "open": "bg-rose-500/20 text-rose-300 border-rose-500/30",
        "triaged": "bg-amber-500/20 text-amber-300 border-amber-500/30",
        "fixed": "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
        "verified": "bg-sky-500/20 text-sky-300 border-sky-500/30",
        "closed": "bg-slate-600/40 text-slate-400 border-slate-600/40",
    }.get(updated.status, "bg-slate-700 text-slate-300")

    return HTMLResponse(
        content=f'<span class="px-2 py-0.5 rounded-full border text-xs font-semibold {badge_color}">{updated.status.capitalize()}</span>',
    )
