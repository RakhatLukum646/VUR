"""LLM Service - FastAPI application for sign language translation."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.processors.sentence_builder import SentenceBuilder
from app.routers import translate_router, health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global rate limiter — keyed by client IP.
# Translate endpoint is limited to 30 req/min to control Gemini API costs.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if not settings.is_configured:
        logger.warning("GEMINI_API_KEY not set. Running in fallback mode.")
    else:
        logger.info(f"Configuration loaded — model: {settings.GEMINI_MODEL}")

    builder = SentenceBuilder()
    app.state.sentence_builder = builder

    logger.info(f"LLM Service started on port {settings.PORT}")

    yield

    logger.info("Shutting down LLM Service...")


app = FastAPI(
    title="Sign Language LLM Service",
    description="Natural language translation for sign language detection",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(translate_router)
app.include_router(health_router)


@app.get("/")
async def root():
    return {
        "service": "Sign Language LLM Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL,
    )
