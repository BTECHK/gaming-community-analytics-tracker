"""Data source adapters for various platforms."""

from app.ingestion.adapters.base import DataSourceAdapter, IngestedPost
from app.ingestion.adapters.youtube import (
    YouTubeAdapter,
    YouTubeQuotaError,
    YouTubeQuotaTracker,
    get_quota_tracker,
)

__all__ = [
    "DataSourceAdapter",
    "IngestedPost",
    "YouTubeAdapter",
    "YouTubeQuotaError",
    "YouTubeQuotaTracker",
    "get_quota_tracker",
]
