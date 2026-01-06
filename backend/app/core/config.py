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

    # SMTP Email Configuration (for annual review reminders)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@anscheckt.nl"
    SMTP_FROM_NAME: str = "AnsCheckt"
    SMTP_USE_TLS: bool = True

    # Admin email for notifications
    ADMIN_EMAIL: Optional[str] = None

    # Data Retention Periods (in days) - Issue #91
    RETENTION_UNPUBLISHED_SUBMISSIONS_DAYS: int = 90  # Unpublished submissions
    RETENTION_AUDIT_LOGS_DAYS: int = 2555  # 7 years (365 * 7)
    RETENTION_DRAFT_EVIDENCE_DAYS: int = 730  # 2 years
    RETENTION_REJECTED_CLAIMS_DAYS: int = 365  # 1 year
    RETENTION_CORRECTION_REQUESTS_DAYS: int = 1095  # 3 years

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into list of origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)


# Global settings instance
settings = Settings()
