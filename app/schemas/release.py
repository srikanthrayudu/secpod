import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field

class ReleaseBase(BaseModel):
    name: str = Field(..., max_length=100)
    target_date: date | None = None
    status: str = "planned"  # 'planned', 'in_progress', 'released'

class ReleaseCreate(ReleaseBase):
    pass

class ReleaseUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    target_date: date | None = None
    status: str | None = None

class ReleaseResponse(ReleaseBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
