"""FastAPI application entry point for MediaPipe service."""

import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health_router, websocket_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("media_pipe_service")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI lifecycle hooks."""
    logger.info("startup service=media_pipe port=%s", settings.PORT)
    logger.info("hand_detection_ready service=media_pipe")
    logger.info(
        "websocket_ready service=media_pipe path=/ws/sign-detection port=%s",
        settings.PORT,
    )
    yield
    logger.info("shutdown service=media_pipe")


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_observability(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed service=media_pipe method=%s path=%s request_id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                (perf_counter() - started_at) * 1000,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed service=media_pipe method=%s path=%s status_code=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
        )
        return response

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
        log_level=settings.LOG_LEVEL.lower(),
    )
