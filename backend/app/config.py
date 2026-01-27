"""Pydantic Settings for environment variable management."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str  # postgresql+asyncpg://user:pass@db:5432/communitypulse

    # Valkey/Redis (use redis:// protocol - valkey is wire-compatible)
    valkey_url: str = "redis://cache:6379/0"

    # Security
    secret_key: str
    debug: bool = False

    # Application
    app_name: str = "CommunityPulse API"

    # YouTube API
    youtube_api_key: str = ""
    youtube_channel_ids: list[str] = []  # e.g., ["UC2t5bjwHdUX4vM2g8TRDq5g"]
    youtube_search_queries: list[str] = []  # e.g., ["gaming"]
    youtube_fetch_limit: int = 50  # Videos per channel
    youtube_daily_quota_limit: int = 9000  # Safety buffer below 10k free tier

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
