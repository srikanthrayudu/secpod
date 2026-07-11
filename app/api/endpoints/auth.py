from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from app.api import deps
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import Token, ChangePasswordRequest
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.auth import AuthService
import jwt

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    return await auth_service.register_user(user_in)

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # Store token in cookie for browser/HTMX support
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800, # 30 mins
        samesite="lax"
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=Token)
async def refresh(
    response: Response,
    refresh_token: str,
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token."
            )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired or invalid refresh token."
        )

    user = await auth_service.get_user_profile(user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access}",
        httponly=True,
        max_age=1800,
        samesite="lax"
    )

    return Token(access_token=new_access, refresh_token=new_refresh)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(deps.get_current_active_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    return await auth_service.update_user_profile(current_user.id, update_in)

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(deps.get_current_active_user),
    auth_service: AuthService = Depends(deps.get_auth_service)
):
    # Verify old password
    await auth_service.authenticate_user(current_user.email, payload.old_password)
    # Update to new password
    await auth_service.update_user_profile(current_user.id, UserUpdate(password=payload.new_password))
    return {"message": "Password changed successfully."}
