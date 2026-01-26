"""CommunityPulse API - FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.api.routes import health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: application ready
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="CommunityPulse API",
        description="the game Community Sentiment Dashboard API",
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
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])

    return app


app = create_app()
