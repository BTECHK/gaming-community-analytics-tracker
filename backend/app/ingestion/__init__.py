"""Data ingestion module."""

from app.ingestion.service import IngestionService, upsert_posts

__all__ = ["IngestionService", "upsert_posts"]
