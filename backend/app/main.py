"""CommunityPulse API - FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="CommunityPulse API",
    description="gaming community sentiment aggregator",
    version="0.1.0",
)


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "CommunityPulse API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
