import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.schemas.release import ReleaseCreate, ReleaseResponse
from app.services.release_service import ReleaseService
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ReleaseResponse, status_code=status.HTTP_201_CREATED)
async def create_release(
    obj_in: ReleaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_lead)
):
    service = ReleaseService(db)
    return await service.create_release(obj_in)

@router.get("", response_model=list[ReleaseResponse])
async def list_releases(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = ReleaseService(db)
    return await service.get_releases(skip=skip, limit=limit)

@router.get("/{id}/readiness")
async def get_release_readiness(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = ReleaseService(db)
    return await service.get_readiness(id)
