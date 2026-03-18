from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="VUR Auth Service")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)

    @app.get("/")
    async def root():
        return {"message": "Auth service is running"}

    return app


app = create_app()
