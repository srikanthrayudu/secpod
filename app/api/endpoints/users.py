from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.api import deps
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    role: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    user_repo: UserRepository = Depends(deps.get_user_repository),
    current_user: User = Depends(deps.get_current_admin_user)
):
    users, total = await user_repo.get_users_paged(
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(deps.get_user_repository),
    current_user: User = Depends(deps.get_current_admin_user)
):
    user = await user_repo.get(user_id)
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    update_in: UserUpdate,
    auth_service: AuthService = Depends(deps.get_auth_service),
    current_user: User = Depends(deps.get_current_admin_user)
):
    return await auth_service.update_user_profile(user_id, update_in)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    user_repo: UserRepository = Depends(deps.get_user_repository),
    current_user: User = Depends(deps.get_current_admin_user)
):
    await user_repo.remove(user_id)
    return None
