"""CloudDesk FastAPI application entrypoint.

Initializes logging, middleware stack (CORS -> RequestId), and unprefixed health routes.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.database import create_tables
from backend.app.core.logging import setup_logging
from backend.app.middleware.request_id import RequestIdMiddleware
from backend.app.services.seed_service import bootstrap_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown hooks."""
    setup_logging()
    settings = get_settings()

    if settings.DEMO_MODE:
        await create_tables()
        await bootstrap_demo_data()

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="CloudDesk",
        version="0.1.0",
        description="CloudDesk — Autonomous Customer Support & Resolution Platform",
        lifespan=lifespan,
    )

    # Middleware order: outermost last
    # Requests flow: CORS -> RequestId -> Endpoints
    # In Starlette, middlewares wrap in reverse order of addition
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Mount unprefixed health routes (/health, /health/live, /health/ready)
    app.include_router(health_router)

    return app


app = create_app()

