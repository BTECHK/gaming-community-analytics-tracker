"""Data source adapters for various platforms."""

from app.ingestion.adapters.base import DataSourceAdapter, IngestedPost
from app.ingestion.adapters.youtube import (
    YouTubeAdapter,
    YouTubeQuotaError,
    YouTubeQuotaTracker,
    get_quota_tracker,
)
from app.ingestion.adapters.official_news import RiotAdapter
from app.ingestion.adapters.tiersite import TierSiteAdapter
from app.ingestion.adapters.google_trends import GoogleTrendsAdapter
from app.ingestion.adapters.guidesite import GuideSiteAdapter

__all__ = [
    "DataSourceAdapter",
    "IngestedPost",
    "YouTubeAdapter",
    "YouTubeQuotaError",
    "YouTubeQuotaTracker",
    "get_quota_tracker",
    "RiotAdapter",
    "TierSiteAdapter",
    "GoogleTrendsAdapter",
    "GuideSiteAdapter",
]
