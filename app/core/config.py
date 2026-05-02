from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Configuration
    APP_ENV: Literal["development", "production"] = "development"
    
    # Database Configuration
    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # JWT Configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MinIO (S3-compatible) Storage Configuration
    # Change MINIO_BUCKET in .env to switch upload bucket
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "uploads"
    MINIO_SECURE: bool = False
    # Optional public endpoint for URL generation (defaults to MINIO_ENDPOINT)
    MINIO_PUBLIC_ENDPOINT: str | None = None

    # SMTP (optional). When host is set (SMTP_HOST or SMTP_SERVER), customer OTP emails are sent.
    SMTP_HOST: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_HOST", "SMTP_SERVER"),
    )
    SMTP_PORT: int = 587
    SMTP_USER: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_USER", "SMTP_USERNAME"),
    )
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_FROM_EMAIL", "SENDER_EMAIL"),
    )
    SENDER_NAME: str | None = None
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    # When false, customer OTP emails are never sent (OTP still created; use development_otp in dev).
    EMAIL_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def database_url(self) -> str:
        """Construct async MySQL database URL"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.APP_ENV == "production"


# Global settings instance
settings = Settings()
