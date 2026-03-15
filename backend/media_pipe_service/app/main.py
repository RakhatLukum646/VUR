"""FastAPI application entry point for MediaPipe service."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.routers import websocket_router, health_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="MediaPipe Sign Language Service",
        description="Real-time hand gesture detection for sign language translation",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(websocket_router)
    
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        print(f"🚀 MediaPipe Service starting on port {settings.PORT}")
        print(f"📹 Hand detection ready")
        print(f"🌐 WebSocket endpoint: ws://localhost:{settings.PORT}/ws/sign-detection")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        print("👋 MediaPipe Service shutting down")
    
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
