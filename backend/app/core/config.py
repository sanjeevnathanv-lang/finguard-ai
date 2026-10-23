import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="FinGuard AI")
    VERSION: str = "0.1.0"
    DATABASE_URL: str = Field(default="sqlite:///./finguard.db")
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ]
    JWT_SECRET: str = Field(default="finguard-ai-local-dev-secret-change-in-production-2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_MINUTES: int = 15
    CSV_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    CSV_MAX_ROW_COUNT: int = 10000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
