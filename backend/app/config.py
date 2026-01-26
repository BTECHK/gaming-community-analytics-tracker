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

    # Reddit API credentials
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "communitypulse:v0.1.0 (by /u/communitypulse_dev)"

    # Reddit ingestion settings
    reddit_subreddits: list[str] = ["gamecommunity"]
    reddit_fetch_limit: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
