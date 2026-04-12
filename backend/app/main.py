"""CommunityPulse API - FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.api.routes import health, ingestion, dashboard, feedback, nlp

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_optional_apis():
    """Check for optional API keys and log warnings if not set."""
    if not settings.gemini_api_key:
        logger.warning(
            "GEMINI_API_KEY not set - using fallback topic naming. "
            "Set GEMINI_API_KEY for AI-powered features."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    from app.ingestion.scheduler import scheduler_lifespan

    await check_optional_apis()
    async with scheduler_lifespan():
        yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="CommunityPulse API",
        description="Gaming Community Sentiment Dashboard API",
        version="0.1.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Security headers middleware (must be added first to wrap all responses)
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(ingestion.router, prefix="/api", tags=["ingestion"])
    app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
    app.include_router(feedback.router, prefix="/api", tags=["feedback"])
    app.include_router(nlp.router, prefix="/api", tags=["nlp"])

    return app


app = create_app()
