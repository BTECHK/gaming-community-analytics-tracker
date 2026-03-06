"""Mock implementation of ValkeyJobStore for testing without Redis/Valkey."""

import json
from datetime import datetime
from typing import Any


class MockValkeyJobStore:
    """In-memory mock implementation of ValkeyJobStore for testing.

    Provides the same interface as ValkeyJobStore but uses an in-memory
    dictionary for storage instead of Redis/Valkey.
    """

    _instance: "MockValkeyJobStore | None" = None
    _storage: dict[str, Any]
    _ttls: dict[str, int]  # Track TTLs for completeness
    _job_counter: int

    def __init__(self) -> None:
        """Initialize the mock store with empty storage."""
        self._storage = {}
        self._ttls = {}
        self._job_counter = 0

    @classmethod
    async def get_instance(cls) -> "MockValkeyJobStore":
        """Get or create the singleton instance.

        Returns:
            MockValkeyJobStore instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance and storage.

        Call this between tests to ensure isolation.
        """
        cls._instance = None

    async def close(self) -> None:
        """Close the mock store (no-op, but matches interface)."""
        MockValkeyJobStore._instance = None

    async def set_job_state(self, job_data: dict[str, Any]) -> None:
        """Store current job state.

        Args:
            job_data: Job progress data to persist.
        """
        serialized = self._serialize_job_data(job_data)
        self._storage["nlp:job:current"] = json.dumps(serialized)
        self._ttls["nlp:job:current"] = 86400  # 24 hours

    async def get_job_state(self) -> dict[str, Any] | None:
        """Get current job state.

        Returns:
            Job data dict or None if no job exists.
        """
        data = self._storage.get("nlp:job:current")
        if data is None:
            return None
        try:
            job_data = json.loads(data)
            return self._deserialize_job_data(job_data)
        except json.JSONDecodeError:
            return None

    async def clear_job_state(self) -> None:
        """Clear the current job state."""
        self._storage.pop("nlp:job:current", None)
        self._ttls.pop("nlp:job:current", None)

    async def set_last_trigger(self, timestamp: datetime) -> None:
        """Store the timestamp of the last job trigger.

        Args:
            timestamp: When the job was triggered.
        """
        self._storage["nlp:job:last_trigger"] = timestamp.isoformat()
        self._ttls["nlp:job:last_trigger"] = 3600  # 1 hour

    async def get_last_trigger(self) -> datetime | None:
        """Get the timestamp of the last job trigger.

        Returns:
            Datetime of last trigger or None.
        """
        data = self._storage.get("nlp:job:last_trigger")
        if data is None:
            return None
        try:
            return datetime.fromisoformat(data)
        except ValueError:
            return None

    async def increment_job_counter(self) -> int:
        """Increment and return the job counter for unique IDs.

        Returns:
            New counter value.
        """
        self._job_counter += 1
        return self._job_counter

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
        """Check mock store health (always connected).

        Returns:
            Dict with connection status.
        """
        return {"status": "connected", "error": None}

    # Additional utility methods for testing

    def get_storage(self) -> dict[str, Any]:
        """Get the raw storage dict for test assertions."""
        return self._storage.copy()

    def clear_storage(self) -> None:
        """Clear all stored data."""
        self._storage.clear()
        self._ttls.clear()
        self._job_counter = 0
