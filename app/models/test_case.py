import uuid
from sqlalchemy import String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedUUIDModel

class TestCase(TimeStampedUUIDModel):
    __tablename__ = "test_cases"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    module: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)  # 'low', 'medium', 'high', 'critical'
    steps: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # Ordered list of steps
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # List of tags (strings)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship("User")
    test_runs: Mapped[list["TestRun"]] = relationship("TestRun", back_populates="test_case", cascade="all, delete-orphan")
