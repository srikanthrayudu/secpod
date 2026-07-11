import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class DefectBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    severity: str = Field(..., max_length=50)  # 'low', 'medium', 'high', 'critical'
    status: str = "open"  # 'open', 'triaged', 'fixed', 'verified', 'closed'
    test_run_id: uuid.UUID | None = None

class DefectCreate(DefectBase):
    pass

class DefectUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    test_run_id: uuid.UUID | None = None
    resolved_at: datetime | None = None

class DefectResponse(DefectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None

    class Config:
        from_attributes = True
