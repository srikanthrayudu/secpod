from fastapi import APIRouter, Depends, Request, Response, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.test_case import TestCase
from app.models.test_run import TestRun
from app.models.defect import Defect
from app.models.release import Release
from app.repositories.user import UserRepository
from app.schemas.user import UserUpdate
from app.services.auth import AuthService
from app.utils.logger import logger
from uuid import UUID

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None
# Expose app settings to all templates globally (e.g. {{ settings.LLM_MODEL }})
templates.env.globals["settings"] = settings

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    user_repo: UserRepository = Depends(deps.get_user_repository),
):
    _, total_users = await user_repo.get_users_paged(limit=1)

    tc_count = (await db.execute(select(func.count(TestCase.id)).filter(TestCase.archived == False))).scalar() or 0
    total_runs = (await db.execute(select(func.count(TestRun.id)))).scalar() or 0
    passed_runs = (await db.execute(select(func.count(TestRun.id)).filter(TestRun.status == "passed"))).scalar() or 0
    open_defects = (await db.execute(select(func.count(Defect.id)).filter(Defect.status.in_(["open", "triaged"])))).scalar() or 0
    pass_rate = round(passed_runs / total_runs * 100) if total_runs else 0
    active_releases = (await db.execute(select(func.count(Release.id)).filter(Release.status.in_(["planned", "in_progress"])))).scalar() or 0

    recent_runs_result = await db.execute(
        select(TestRun).order_by(TestRun.created_at.desc()).limit(8)
    )
    recent_runs = list(recent_runs_result.scalars().all())

    stats = {
        "total_users": total_users,
        "test_cases": tc_count,
        "total_runs": total_runs,
        "pass_rate": pass_rate,
        "open_defects": open_defects,
        "active_releases": active_releases,
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "user": current_user,
            "stats": stats,
            "recent_runs": recent_runs,
            "active_tab": "dashboard",
        },
    )

@router.get("/dashboard/users", response_class=HTMLResponse)
async def dashboard_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(deps.get_current_active_user),
    user_repo: UserRepository = Depends(deps.get_user_repository)
):
    # Only admin can manage users, standard user redirected or error shown
    if current_user.role != "admin":
        return templates.TemplateResponse(
            request=request,
            name="dashboard/error.html",
            context={"user": current_user, "message": "Only administrators can view this page.", "active_tab": "users"}
        )

    users, total = await user_repo.get_users_paged(
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        sort_by=sort_by,
        sort_order=sort_order
    )

    page = (skip // limit) + 1
    total_pages = (total + limit - 1) // limit

    context = {
        "request": request,
        "user": current_user,
        "users": users,
        "skip": skip,
        "limit": limit,
        "search": search or "",
        "role": role or "",
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "total_pages": total_pages,
        "total_count": total,
        "active_tab": "users"
    }

    # If it's an HTMX request, we swap only the table partial to avoid full reload
    if request.headers.get("hx-request"):
        return templates.TemplateResponse(request=request, name="dashboard/users_table.html", context=context)

    return templates.TemplateResponse(request=request, name="dashboard/users.html", context=context)

@router.get("/dashboard/profile", response_class=HTMLResponse)
async def dashboard_profile(
    request: Request,
    current_user: User = Depends(deps.get_current_active_user)
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard/profile.html", 
        context={"user": current_user, "active_tab": "profile", "success": None, "error": None}
    )

@router.post("/dashboard/profile", response_class=HTMLResponse)
async def dashboard_profile_update(
    request: Request,
    full_name: str = Form(None),
    bio: str = Form(None),
    company: str = Form(None),
    location: str = Form(None),
    password: str = Form(None),
    current_user: User = Depends(deps.get_current_active_user),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    try:
        update_data = UserUpdate(
            full_name=full_name,
            bio=bio,
            company=company,
            location=location
        )
        if password and len(password.strip()) >= 6:
            update_data.password = password
            
        updated_user = await auth_service.update_user_profile(current_user.id, update_data)
        
        # If HTMX request, we return a partial save button/success toast or form
        if request.headers.get("hx-request"):
            return templates.TemplateResponse(
                request=request,
                name="dashboard/profile_card.html",
                context={"user": updated_user, "success": "Profile updated successfully!"}
            )
            
        return templates.TemplateResponse(
            request=request,
            name="dashboard/profile.html",
            context={"user": updated_user, "active_tab": "profile", "success": "Profile updated successfully!"}
        )
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return templates.TemplateResponse(
            request=request,
            name="dashboard/profile.html",
            context={"user": current_user, "active_tab": "profile", "error": "Failed to update profile."}
        )

@router.get("/dashboard/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_modal(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(deps.get_current_admin_user),
    user_repo: UserRepository = Depends(deps.get_user_repository)
):
    user = await user_repo.get(user_id)
    return templates.TemplateResponse(request=request, name="dashboard/user_edit_modal.html", context={"target_user": user})

@router.post("/dashboard/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_action(
    request: Request,
    user_id: UUID,
    full_name: str = Form(None),
    role: str = Form(None),
    is_active: bool = Form(False),
    is_verified: bool = Form(False),
    current_user: User = Depends(deps.get_current_admin_user),
    auth_service: AuthService = Depends(deps.get_auth_service),
    user_repo: UserRepository = Depends(deps.get_user_repository)
):
    update_data = UserUpdate(
        full_name=full_name,
        role=role,
        is_active=is_active,
        is_verified=is_verified
    )
    await auth_service.update_user_profile(user_id, update_data)
    
    # Return HTMX response to close modal and refresh list
    response = HTMLResponse(content="")
    response.headers["HX-Trigger"] = "userUpdated"
    return response

@router.delete("/dashboard/users/{user_id}", response_class=HTMLResponse)
async def delete_user_action(
    user_id: UUID,
    request: Request,
    current_user: User = Depends(deps.get_current_admin_user),
    user_repo: UserRepository = Depends(deps.get_user_repository)
):
    await user_repo.remove(user_id)

    # If it's an HTMX request, we return blank content to remove the row and update stats via OOB swap
    if request.headers.get("hx-request"):
        # Get updated stats
        _, total_users = await user_repo.get_users_paged(limit=1)

        # Mock system metrics (in a real app, these would come from actual services)
        stats = {
            "total_users": total_users,
        }

        # Return HTML with OOB swap for stats and empty content for row removal
        html_content = f"""
            <div id="total-users-stat" hx-swap-oob="true">
                <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800/60 shadow-md">
                    <div class="flex items-center justify-between text-slate-500">
                        <span class="text-xs font-semibold uppercase tracking-wider">Team Members</span>
                        <svg class="h-5 w-5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    </div>
                    <p class="mt-3 text-3xl font-bold tracking-tight">{stats['total_users']}</p>
                    <span class="block mt-1 text-[10px] text-emerald-400 font-medium">Active accounts</span>
                </div>
            </div>
        """
        return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)

    # Return blank content to remove the row from the DOM (non-HTMX fallback)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
