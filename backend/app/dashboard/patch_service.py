"""Patch service for detecting current game patch version from Data Dragon."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

__all__ = ["PatchService"]

# Data Dragon versions endpoint
VERSIONS_URL = "https://ddragon.gamecommunity.com/api/versions.json"

# Cache configuration
_cache: Optional[tuple[str, datetime]] = None
_cache_ttl = timedelta(hours=1)


class PatchService:
    """Service for fetching current game patch version from Data Dragon.

    Caches the patch version for 1 hour to avoid excessive API calls.
    """

    async def get_current_patch(self) -> str:
        """Get the current game patch version.

        Fetches from Data Dragon API and extracts major.minor version.
        Results are cached for 1 hour.

        Returns:
            Patch version string (e.g., "16.2") or "unknown" on failure.
        """
        global _cache

        # Check cache
        if _cache is not None:
            version, timestamp = _cache
            if datetime.now(timezone.utc) - timestamp < _cache_ttl:
                logger.debug("Using cached patch version: %s", version)
                return version

        # Fetch from Data Dragon
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(VERSIONS_URL)
                response.raise_for_status()

                versions = response.json()
                if not versions or not isinstance(versions, list):
                    logger.warning("Invalid versions response from Data Dragon")
                    return self._get_fallback_version()

                # First entry is always the current version (e.g., "16.2.1")
                full_version = versions[0]

                # Extract major.minor (e.g., "16.2" from "16.2.1")
                parts = full_version.split(".")
                if len(parts) >= 2:
                    patch_version = f"{parts[0]}.{parts[1]}"
                else:
                    patch_version = full_version

                # Update cache
                _cache = (patch_version, datetime.now(timezone.utc))
                logger.info("Fetched current patch version: %s", patch_version)
                return patch_version

        except httpx.HTTPError as e:
            logger.error("Failed to fetch patch version from Data Dragon: %s", e)
            return self._get_fallback_version()
        except Exception as e:
            logger.error("Unexpected error fetching patch version: %s", e)
            return self._get_fallback_version()

    def _get_fallback_version(self) -> str:
        """Get fallback version from cache or return unknown.

        Returns:
            Cached version if available, otherwise "unknown".
        """
        global _cache
        if _cache is not None:
            version, _ = _cache
            logger.info("Using stale cached patch version: %s", version)
            return version
        return "unknown"
