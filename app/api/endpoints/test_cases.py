import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.database import get_db
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from app.services.test_case_service import TestCaseService
from app.models.user import User

router = APIRouter()

@router.get("", response_model=list[TestCaseResponse])
async def list_test_cases(
    module: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = TestCaseService(db)
    return await service.get_test_cases(
        module=module,
        priority=priority,
        search=search,
        include_archived=include_archived,
        skip=skip,
        limit=limit
    )

@router.post("", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_test_case(
    obj_in: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_engineer)
):
    service = TestCaseService(db)
    return await service.create_test_case(obj_in, current_user.id)

@router.get("/{id}", response_model=TestCaseResponse)
async def get_test_case(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    service = TestCaseService(db)
    test_case = await service.get_test_case(id)
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.")
    return test_case

@router.patch("/{id}", response_model=TestCaseResponse)
async def update_test_case(
    id: uuid.UUID,
    obj_in: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_engineer)
):
    service = TestCaseService(db)
    test_case = await service.get_test_case(id)
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.")
    return await service.update_test_case(test_case, obj_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_case(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_qa_lead)
):
    service = TestCaseService(db)
    test_case = await service.get_test_case(id)
    if not test_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found.")
    await service.delete_test_case(id)
