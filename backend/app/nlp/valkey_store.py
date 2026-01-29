"""Valkey/Redis store for NLP job state persistence."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)

# Key prefixes
KEY_JOB_CURRENT = "nlp:job:current"
KEY_JOB_LAST_TRIGGER = "nlp:job:last_trigger"
KEY_JOB_COUNTER = "nlp:job:counter"

# TTL values
JOB_STATE_TTL = 86400  # 24 hours
LAST_TRIGGER_TTL = 3600  # 1 hour


class ValkeyJobStore:
    """Persistent storage for NLP job state using Valkey/Redis.

    Provides async operations for job state, rate limiting, and progress tracking.
    Valkey is wire-compatible with Redis, so we use redis-py with async support.
    """

    _instance: "ValkeyJobStore | None" = None
    _client: redis.Redis | None = None

    @classmethod
    async def get_instance(cls) -> "ValkeyJobStore":
        """Get or create the singleton instance.

        Returns:
            ValkeyJobStore instance with connected client.
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
            logger.info("Connected to Valkey for job state persistence")
        except Exception as e:
            logger.error("Failed to connect to Valkey: %s", e)
            raise

    @property
    def client(self) -> redis.Redis:
        """Get the Redis client, raising if not connected."""
        if self._client is None:
            raise RuntimeError("ValkeyJobStore not connected. Call get_instance() first.")
        return self._client

    async def close(self) -> None:
        """Close the Valkey connection."""
        if self._client:
            await self._client.close()
            self._client = None
            ValkeyJobStore._instance = None

    async def set_job_state(self, job_data: dict[str, Any]) -> None:
        """Store current job state.

        Args:
            job_data: Job progress data to persist.
        """
        # Serialize datetime fields
        serialized = self._serialize_job_data(job_data)
        await self.client.setex(
            KEY_JOB_CURRENT,
            JOB_STATE_TTL,
            json.dumps(serialized),
        )

    async def get_job_state(self) -> dict[str, Any] | None:
        """Get current job state.

        Returns:
            Job data dict or None if no job exists.
        """
        data = await self.client.get(KEY_JOB_CURRENT)
        if data is None:
            return None
        try:
            job_data = json.loads(data)
            return self._deserialize_job_data(job_data)
        except json.JSONDecodeError:
            logger.warning("Failed to decode job state from Valkey")
            return None

    async def clear_job_state(self) -> None:
        """Clear the current job state."""
        await self.client.delete(KEY_JOB_CURRENT)

    async def set_last_trigger(self, timestamp: datetime) -> None:
        """Store the timestamp of the last job trigger.

        Args:
            timestamp: When the job was triggered.
        """
        await self.client.setex(
            KEY_JOB_LAST_TRIGGER,
            LAST_TRIGGER_TTL,
            timestamp.isoformat(),
        )

    async def get_last_trigger(self) -> datetime | None:
        """Get the timestamp of the last job trigger.

        Returns:
            Datetime of last trigger or None.
        """
        data = await self.client.get(KEY_JOB_LAST_TRIGGER)
        if data is None:
            return None
        try:
            return datetime.fromisoformat(data)
        except ValueError:
            logger.warning("Failed to parse last trigger timestamp")
            return None

    async def increment_job_counter(self) -> int:
        """Increment and return the job counter for unique IDs.

        Returns:
            New counter value.
        """
        return await self.client.incr(KEY_JOB_COUNTER)

    def _serialize_job_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Serialize job data for storage.

        Converts datetime objects to ISO strings.
        """
        result = data.copy()
        for key in ["started_at", "completed_at"]:
            if key in result and result[key] is not None:
                if isinstance(result[key], datetime):
                    result[key] = result[key].isoformat()
        return result

    def _deserialize_job_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deserialize job data from storage.

        Converts ISO strings back to datetime objects.
        """
        result = data.copy()
        for key in ["started_at", "completed_at"]:
            if key in result and result[key] is not None:
                if isinstance(result[key], str):
                    try:
                        result[key] = datetime.fromisoformat(result[key])
                    except ValueError:
                        result[key] = None
        return result

    async def health_check(self) -> dict[str, Any]:
        """Check Valkey connection health.

        Returns:
            Dict with connection status.
        """
        try:
            await self.client.ping()
            return {"status": "connected", "error": None}
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}
