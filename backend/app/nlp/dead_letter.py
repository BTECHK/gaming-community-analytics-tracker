"""Dead Letter Queue for failed NLP processing attempts."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

# Key prefixes
KEY_DLQ_POSTS = "nlp:dlq:posts"  # Set of post IDs
KEY_DLQ_DETAIL_PREFIX = "nlp:dlq:detail:"  # Hash for each post

# Configuration
MAX_RETRIES = 3
DLQ_TTL = 604800  # 7 days


class DeadLetterQueue:
    """Dead Letter Queue for tracking failed post processing.

    Stores failed posts with error details, retry count, and timestamps.
    Uses Valkey/Redis for persistence.
    """

    _instance: "DeadLetterQueue | None" = None
    _client: redis.Redis | None = None

    @classmethod
    async def get_instance(cls) -> "DeadLetterQueue":
        """Get or create the singleton instance.

        Returns:
            DeadLetterQueue instance with connected client.
        """
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._connect()
        return cls._instance

    async def _connect(self) -> None:
        """Establish connection to Valkey."""
        settings = get_settings()
        try:
            self._client = redis.from_url(
                settings.valkey_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
            logger.info("Connected to Valkey for dead letter queue")
        except Exception as e:
            logger.error("Failed to connect to Valkey for DLQ: %s", e)
            raise

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("DeadLetterQueue not connected. Call get_instance() first.")
        return self._client

    async def close(self) -> None:
        """Close the Valkey connection."""
        if self._client:
            await self._client.close()
            self._client = None
            DeadLetterQueue._instance = None

    async def add_failed_post(
        self,
        post_id: str,
        error: str,
        post_content: str | None = None,
    ) -> dict[str, Any]:
        """Add a failed post to the dead letter queue.

        If the post already exists, increments the retry count.

        Args:
            post_id: Unique identifier of the failed post.
            error: Error message describing the failure.
            post_content: Optional post content for debugging.

        Returns:
            Dict with post DLQ entry details.
        """
        detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"
        now = datetime.now(timezone.utc).isoformat()

        # Check if already in DLQ
        existing = await self.client.hgetall(detail_key)

        if existing:
            # Increment retry count
            retry_count = int(existing.get("retry_count", 0)) + 1
            errors_json = existing.get("errors", "[]")
            try:
                errors = json.loads(errors_json)
            except json.JSONDecodeError:
                errors = []
            errors.append({"error": error, "timestamp": now})

            await self.client.hset(
                detail_key,
                mapping={
                    "retry_count": str(retry_count),
                    "last_attempt": now,
                    "last_error": error,
                    "errors": json.dumps(errors[-10:]),  # Keep last 10 errors
                },
            )
            await self.client.expire(detail_key, DLQ_TTL)

            return {
                "post_id": post_id,
                "retry_count": retry_count,
                "can_retry": retry_count < MAX_RETRIES,
            }
        else:
            # New DLQ entry
            entry = {
                "post_id": post_id,
                "first_failure": now,
                "last_attempt": now,
                "last_error": error,
                "retry_count": "1",
                "errors": json.dumps([{"error": error, "timestamp": now}]),
            }
            if post_content:
                entry["content_preview"] = post_content[:500]

            await self.client.hset(detail_key, mapping=entry)
            await self.client.expire(detail_key, DLQ_TTL)
            await self.client.sadd(KEY_DLQ_POSTS, post_id)

            return {
                "post_id": post_id,
                "retry_count": 1,
                "can_retry": True,
            }

    async def should_retry(self, post_id: str) -> bool:
        """Check if a post should be retried.

        Args:
            post_id: Post identifier.

        Returns:
            True if under retry limit, False otherwise.
        """
        detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"
        retry_count = await self.client.hget(detail_key, "retry_count")

        if retry_count is None:
            return True  # Not in DLQ, can try

        return int(retry_count) < MAX_RETRIES

    async def remove_post(self, post_id: str) -> bool:
        """Remove a post from the dead letter queue.

        Call this when a post is successfully processed or should be abandoned.

        Args:
            post_id: Post identifier.

        Returns:
            True if removed, False if not found.
        """
        detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"

        # Check if exists
        exists = await self.client.exists(detail_key)
        if not exists:
            return False

        # Remove from both the detail hash and the set
        await self.client.delete(detail_key)
        await self.client.srem(KEY_DLQ_POSTS, post_id)

        logger.info("Removed post %s from DLQ", post_id)
        return True

    async def get_failed_posts(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get list of failed posts in the DLQ.

        Args:
            limit: Maximum number of posts to return.
            offset: Number of posts to skip.

        Returns:
            List of post details.
        """
        # Get all post IDs from the set
        post_ids = await self.client.smembers(KEY_DLQ_POSTS)

        if not post_ids:
            return []

        # Sort for consistent ordering and apply pagination
        sorted_ids = sorted(post_ids)
        paginated_ids = sorted_ids[offset : offset + limit]

        results = []
        for post_id in paginated_ids:
            detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"
            details = await self.client.hgetall(detail_key)

            if details:
                entry = {
                    "post_id": post_id,
                    "retry_count": int(details.get("retry_count", 0)),
                    "first_failure": details.get("first_failure"),
                    "last_attempt": details.get("last_attempt"),
                    "last_error": details.get("last_error"),
                    "can_retry": int(details.get("retry_count", 0)) < MAX_RETRIES,
                }
                if "content_preview" in details:
                    entry["content_preview"] = details["content_preview"]
                results.append(entry)
            else:
                # Orphaned entry - remove from set
                await self.client.srem(KEY_DLQ_POSTS, post_id)

        return results

    async def get_post_details(self, post_id: str) -> dict[str, Any] | None:
        """Get full details for a specific failed post.

        Args:
            post_id: Post identifier.

        Returns:
            Full post details including error history, or None if not found.
        """
        detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"
        details = await self.client.hgetall(detail_key)

        if not details:
            return None

        errors = []
        if "errors" in details:
            try:
                errors = json.loads(details["errors"])
            except json.JSONDecodeError:
                errors = []

        return {
            "post_id": post_id,
            "retry_count": int(details.get("retry_count", 0)),
            "first_failure": details.get("first_failure"),
            "last_attempt": details.get("last_attempt"),
            "last_error": details.get("last_error"),
            "can_retry": int(details.get("retry_count", 0)) < MAX_RETRIES,
            "errors": errors,
            "content_preview": details.get("content_preview"),
        }

    async def get_stats(self) -> dict[str, Any]:
        """Get DLQ statistics.

        Returns:
            Dict with total count, retryable count, etc.
        """
        post_ids = await self.client.smembers(KEY_DLQ_POSTS)
        total = len(post_ids)

        if total == 0:
            return {
                "total": 0,
                "retryable": 0,
                "exhausted": 0,
                "max_retries": MAX_RETRIES,
            }

        retryable = 0
        exhausted = 0

        for post_id in post_ids:
            detail_key = f"{KEY_DLQ_DETAIL_PREFIX}{post_id}"
            retry_count = await self.client.hget(detail_key, "retry_count")

            if retry_count is not None:
                if int(retry_count) < MAX_RETRIES:
                    retryable += 1
                else:
                    exhausted += 1

        return {
            "total": total,
            "retryable": retryable,
            "exhausted": exhausted,
            "max_retries": MAX_RETRIES,
        }

    async def clear(self) -> int:
        """Clear all entries from the dead letter queue.

        Returns:
            Number of entries cleared.
        """
        post_ids = await self.client.smembers(KEY_DLQ_POSTS)
        count = len(post_ids)

        if count == 0:
            return 0

        # Delete all detail keys
        detail_keys = [f"{KEY_DLQ_DETAIL_PREFIX}{pid}" for pid in post_ids]
        if detail_keys:
            await self.client.delete(*detail_keys)

        # Clear the set
        await self.client.delete(KEY_DLQ_POSTS)

        logger.info("Cleared %d entries from DLQ", count)
        return count
