"""Middleware components for CommunityPulse API."""

from app.middleware.security import SecurityHeadersMiddleware

__all__ = ["SecurityHeadersMiddleware"]
