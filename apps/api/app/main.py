from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import engine
from app.models.user import User
from app.routers.auth import router as auth_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting ChronoTrack API", env=settings.APP_ENV)
    yield
    logger.info("Shutting down ChronoTrack API")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ChronoTrack API",
        version="1.0.0",
        description="Time tracking API for freelancers",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)

    @app.get("/api/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "1.0.0"}

    @app.get("/api/v1/users/me", tags=["users"])
    async def get_me(current_user: User = Depends(get_current_user)) -> dict:
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
        }

    return app


app = create_app()
