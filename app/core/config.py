import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    PROJECT_NAME: str = "QualityHub"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Security
    SECRET_KEY: str = Field(..., min_length=16)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database & Cache
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Configurations
    DEFAULT_LLM_PROVIDER: Literal["mock", "openai", "anthropic"] = "mock"
    OPENAI_API_KEY: str = "mock"
    ANTHROPIC_API_KEY: str = "mock"
    LLM_MODEL: str = "gpt-4o-mini"

    # Mail/SMTP Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@qualityhub.secpod.local"
    EMAILS_FROM_NAME: str = "QualityHub"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        # FastAPI template relies on async engines (asyncpg / aiosqlite)
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif v.startswith("sqlite://") and not v.startswith("sqlite+aiosqlite://"):
            v = v.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return v

settings = Settings()
