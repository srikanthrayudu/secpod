import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.schemas.test_run import TestRunCreate, TestRunResponse
from app.schemas.evidence import EvidenceResponse
from app.services.test_run_service import TestRunService
from app.models.user import User

router = APIRouter()

@router.post("", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_test_run(
    obj_in: TestRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(deps.get_ci_or_active_user),
):
    service = TestRunService(db)
    if current_user and not obj_in.executed_by:
        obj_in = obj_in.model_copy(update={"executed_by": current_user.id})
    return await service.create_test_run(obj_in)

@router.get("", response_model=list[TestRunResponse])
async def list_test_runs(
    release_id: uuid.UUID | None = None,
    status: str | None = None,
    source: str | None = None,
    module: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = TestRunService(db)
    return await service.get_test_runs(
        release_id=release_id,
        status=status,
        source=source,
        module=module,
        skip=skip,
        limit=limit
    )

@router.get("/{id}", response_model=TestRunResponse)
async def get_test_run(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = TestRunService(db)
    test_run = await service.get_test_run(id)
    if not test_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found.")
    return test_run

@router.post("/{id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = TestRunService(db)
    return await service.attach_evidence(id, file)
