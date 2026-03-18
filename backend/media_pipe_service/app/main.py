"""FastAPI application entry point for MediaPipe service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import websocket_router, health_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI lifecycle hooks."""
    print(f"MediaPipe Service starting on port {settings.PORT}")
    print("Hand detection ready")
    print(f"WebSocket endpoint: ws://localhost:{settings.PORT}/ws/sign-detection")
    yield
    print("MediaPipe Service shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title="MediaPipe Sign Language Service",
        description="Real-time hand gesture detection for sign language translation",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(websocket_router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
