import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class TestCaseBase(BaseModel):
    title: str = Field(..., max_length=255)
    module: str = Field(..., max_length=100)
    priority: str = Field("medium", max_length=50)  # 'low', 'medium', 'high', 'critical'
    steps: list[str] = Field(default_factory=list)
    expected_result: str
    tags: list[str] | None = None
    archived: bool = False

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    module: str | None = Field(None, max_length=100)
    priority: str | None = None
    steps: list[str] | None = None
    expected_result: str | None = None
    tags: list[str] | None = None
    archived: bool | None = None

class TestCaseResponse(TestCaseBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
