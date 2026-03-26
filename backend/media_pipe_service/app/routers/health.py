"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.routers.websocket import gesture_classifier
    return {
        "status": "healthy",
        "service": "media_pipe",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "model_loaded": gesture_classifier.is_ready,
    }


@health_router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    return {
        "ready": True,
        "service": "media_pipe",
    }
