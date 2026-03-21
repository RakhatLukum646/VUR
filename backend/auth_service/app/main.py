import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.db import ensure_indexes
from app.routers.auth import router as auth_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("auth_service")


async def ensure_db_ready() -> None:
    await ensure_indexes()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("startup service=auth")
    await ensure_db_ready()
    yield
    logger.info("shutdown service=auth")


def create_app() -> FastAPI:
    app = FastAPI(title="VUR Auth Service", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_observability(
        request: Request,
        call_next,
    ):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed service=auth method=%s path=%s request_id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                (perf_counter() - started_at) * 1000,
            )
            raise

        duration_ms = (perf_counter() - started_at) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed service=auth method=%s path=%s status_code=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
        )
        return response

    app.include_router(auth_router)

    try:
        Instrumentator().instrument(app).expose(app)
    except ValueError:
        pass  # Already registered in the global Prometheus registry

    @app.get("/")
    async def root():
        return {"message": "Auth service is running"}

    @app.get("/health")
    async def health():
        return JSONResponse(
            {
                "status": "healthy",
                "service": "auth_service",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    return app


app = create_app()
