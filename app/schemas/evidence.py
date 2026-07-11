import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class EvidenceBase(BaseModel):
    test_run_id: uuid.UUID
    file_path: str = Field(..., max_length=500)
    file_type: str = Field(..., max_length=50)

class EvidenceCreate(EvidenceBase):
    pass

class EvidenceResponse(EvidenceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
