import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedUUIDModel

class Evidence(TimeStampedUUIDModel):
    __tablename__ = "evidence"

    test_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_runs.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'image/png', 'text/plain'

    # Relationships
    test_run: Mapped["TestRun"] = relationship("TestRun", back_populates="evidence")
