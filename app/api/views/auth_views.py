from fastapi import APIRouter, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.api import deps
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import AuthService
from app.core.security import create_access_token, create_refresh_token
from app.utils.logger import logger
import os

router = APIRouter()

# Setup templates path
templates = Jinja2Templates(directory="app/templates")
templates.env.cache = None

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # If already logged in, redirect to dashboard
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="auth/login.html", context={"error": None})

@router.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    try:
        user = await auth_service.authenticate_user(email, password)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        # We redirect to dashboard
        redir = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        redir.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            samesite="lax"
        )
        return redir
    except Exception as e:
        logger.warning(f"Login failed: {e}")
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html", 
            context={"error": "Invalid email or password."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/register.html", context={"error": None})

@router.post("/register", response_class=HTMLResponse)
async def register_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    try:
        user_in = UserCreate(email=email, password=password, full_name=full_name)
        await auth_service.register_user(user_in)
        # Redirect to login page upon success
        return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        logger.warning(f"Registration failed: {e}")
        error_msg = getattr(e, "detail", "Failed to register user. Try another email.")
        return templates.TemplateResponse(
            request=request,
            name="auth/register.html", 
            context={"error": error_msg},
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/logout")
async def logout_view(response: Response):
    redir = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    redir.delete_cookie("access_token")
    return redir

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/forgot_password.html", context={"message": None, "error": None})

@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_action(request: Request, email: str = Form(...)):
    # Simulating email dispatch
    logger.info(f"Simulating forgot password email for: {email}")
    return templates.TemplateResponse(
        request=request,
        name="auth/forgot_password.html", 
        context={"message": "If this email is registered, we have sent link to reset password.", "error": None}
    )
