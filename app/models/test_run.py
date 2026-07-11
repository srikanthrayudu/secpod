import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedUUIDModel

class TestRun(TimeStampedUUIDModel):
    __tablename__ = "test_runs"

    test_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_cases.id"), index=True, nullable=False)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("releases.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # 'passed', 'failed', 'blocked', 'skipped'
    source: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # 'manual', 'automated'
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relationships
    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="test_runs")
    release: Mapped["Release"] = relationship("Release", back_populates="test_runs")
    executor: Mapped["User"] = relationship("User")
    evidence: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="test_run", cascade="all, delete-orphan")
    defect: Mapped["Defect | None"] = relationship("Defect", back_populates="test_run", uselist=False)
