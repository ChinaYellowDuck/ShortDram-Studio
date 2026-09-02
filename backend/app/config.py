"""Application configuration management."""
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "ShortDram Studio"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./shortdram.db"

    # Encryption
    ENCRYPTION_KEY: str = Field(default="")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # Logging
    LOG_LEVEL: str = "info"

    # LangSmith (optional)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "shortdram-studio"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV.lower() == "production"


settings = Settings()
