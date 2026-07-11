from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import TimeStampedUUIDModel

class User(TimeStampedUUIDModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Optional fields for profile details
    bio: Mapped[str] = mapped_column(String(1000), nullable=True)
    company: Mapped[str] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
