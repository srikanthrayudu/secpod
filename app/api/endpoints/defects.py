import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.schemas.defect import DefectCreate, DefectUpdate, DefectResponse
from app.services.defect_service import DefectService
from app.models.user import User

router = APIRouter()

@router.post("", response_model=DefectResponse, status_code=status.HTTP_201_CREATED)
async def create_defect(
    obj_in: DefectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = DefectService(db)
    return await service.create_defect(obj_in)

@router.get("", response_model=list[DefectResponse])
async def list_defects(
    status: str | None = None,
    severity: str | None = None,
    release_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = DefectService(db)
    return await service.get_defects(
        status=status,
        severity=severity,
        release_id=release_id,
        skip=skip,
        limit=limit
    )

@router.patch("/{id}", response_model=DefectResponse)
async def update_defect(
    id: uuid.UUID,
    obj_in: DefectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_lead)
):
    service = DefectService(db)
    defect = await service.get_defect(id)
    if not defect:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Defect not found.")
    return await service.update_defect(defect, obj_in)
