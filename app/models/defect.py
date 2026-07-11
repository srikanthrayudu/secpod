import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedUUIDModel

class Defect(TimeStampedUUIDModel):
    __tablename__ = "defects"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # 'low', 'medium', 'high', 'critical'
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # 'open', 'triaged', 'fixed', 'verified', 'closed'
    test_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("test_runs.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    test_run: Mapped["TestRun | None"] = relationship("TestRun", back_populates="defect")
