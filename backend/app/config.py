"""Pydantic Settings for environment variable management."""

from functools import lru_cache

from pydantic import field_validator
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
    youtube_channel_ids: str = ""  # Comma-separated channel IDs
    youtube_search_queries: str = ""  # Comma-separated search queries
    youtube_fetch_limit: int = 50  # Videos per channel
    youtube_daily_quota_limit: int = 9000  # Safety buffer below 10k free tier

    # OfficialNews News (rito-news-feeds)
    riot_locale: str = "en-us"  # Locale for rito-news-feeds API
    riot_fetch_limit: int = 50  # Max items per fetch

    # TierSite Scraping
    tiersite_fetch_limit: int = 50  # Max items per fetch

    # Google Trends
    google_trends_keywords: str = "gaming,the game patch notes,the game tier list,the game champions"
    google_trends_enabled: bool = True  # Can disable if pytrends breaks

    # GuideSite Scraping
    guidesite_fetch_limit: int = 50  # Max guides per fetch

    # NLP Pipeline
    nlp_batch_size: int = 32
    nlp_chunk_size: int = 1000
    nlp_result_ttl_hours: int = 48
    nlp_enabled: bool = True
    nlp_use_worker: bool = True  # Use isolated worker process for NLP
    nlp_worker_url: str = "http://nlp-worker:8001"  # Worker service URL

    @property
    def google_trends_keywords_list(self) -> list[str]:
        """Parse comma-separated keywords into list."""
        if not self.google_trends_keywords:
            return []
        return [x.strip() for x in self.google_trends_keywords.split(",") if x.strip()]

    @property
    def youtube_channel_ids_list(self) -> list[str]:
        """Parse comma-separated channel IDs into list."""
        if not self.youtube_channel_ids:
            return []
        return [x.strip() for x in self.youtube_channel_ids.split(",") if x.strip()]

    @property
    def youtube_search_queries_list(self) -> list[str]:
        """Parse comma-separated search queries into list."""
        if not self.youtube_search_queries:
            return []
        return [x.strip() for x in self.youtube_search_queries.split(",") if x.strip()]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
