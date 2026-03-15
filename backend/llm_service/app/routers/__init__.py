"""API routers."""
from .translate import router as translate_router
from .health import router as health_router

__all__ = ["translate_router", "health_router"]
