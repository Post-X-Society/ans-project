"""
Application configuration using Pydantic settings
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    APP_NAME: str = "ans-backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/ans_dev"  # Default for dev
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    BENEDMO_API_KEY: Optional[str] = None

    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:3000,https://ans.postxsociety.cloud"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into list of origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
