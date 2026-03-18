"""Health check endpoints."""

from fastapi import APIRouter
from datetime import UTC, datetime

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "media_pipe",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0",
    }


@health_router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    return {
        "ready": True,
        "service": "media_pipe",
    }
