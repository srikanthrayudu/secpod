from datetime import date
from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import TimeStampedUUIDModel

class Release(TimeStampedUUIDModel):
    __tablename__ = "releases"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planned", nullable=False)  # 'planned', 'in_progress', 'released'

    # Relationships
    test_runs: Mapped[list["TestRun"]] = relationship("TestRun", back_populates="release", cascade="all, delete-orphan")
