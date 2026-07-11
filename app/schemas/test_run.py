import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TestRunBase(BaseModel):
    test_case_id: uuid.UUID
    release_id: uuid.UUID
    status: str = Field(..., max_length=50)  # 'passed', 'failed', 'blocked', 'skipped'
    source: str = Field(..., max_length=50)  # 'manual', 'automated'
    duration_ms: int | None = None
    logs: str | None = None
    executed_by: uuid.UUID | None = None

class TestRunCreate(TestRunBase):
    pass

class TestRunUpdate(BaseModel):
    status: str | None = None
    duration_ms: int | None = None
    logs: str | None = None
    executed_by: uuid.UUID | None = None

class TestRunResponse(TestRunBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
