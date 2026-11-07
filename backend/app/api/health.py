"""Health check routes for CloudDesk.

Provides unprefixed, unauthenticated health probes:
- /health: general status and version
- /health/live: liveness probe (no dependency I/O)
- /health/ready: readiness probe (configuration checks; 503 when degraded)
"""

from typing import Any

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from backend.app.core.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """General health probe returning service metadata."""
    return {
        "status": "ok",
        "service": "clouddesk",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def health_live() -> dict[str, str]:
    """Liveness probe. Responds without any dependency I/O."""
    return {
        "status": "alive",
    }


@router.get("/health/ready")
async def health_ready(settings: Settings = Depends(get_settings)) -> Response:
    """Readiness probe. Checks subsystem configurations without external I/O.

    Returns HTTP 200 when all checks are ok, otherwise HTTP 503 degraded.
    Details never include sensitive URLs, passwords, or API keys.
    """
    checks: dict[str, dict[str, Any]] = {}

    # 1. Database configuration
    if settings.DATABASE_URL and settings.DATABASE_URL.strip():
        checks["database"] = {"status": "ok"}
    else:
        checks["database"] = {"status": "error", "detail": "database URL not configured"}

    # 2. Redis configuration (fake redis is valid for offline/demo)
    if settings.USE_FAKE_REDIS or (settings.REDIS_URL and settings.REDIS_URL.strip()):
        checks["redis"] = {"status": "ok"}
    else:
        checks["redis"] = {"status": "error", "detail": "redis URL not configured"}

    # 3. Vector store configuration
    if settings.VECTOR_STORE == "memory":
        checks["vector_store"] = {"status": "ok"}
    elif settings.VECTOR_STORE == "qdrant":
        if settings.QDRANT_URL and settings.QDRANT_URL.strip():
            checks["vector_store"] = {"status": "ok"}
        else:
            checks["vector_store"] = {"status": "error", "detail": "qdrant URL not configured"}
    else:
        checks["vector_store"] = {"status": "error", "detail": "unsupported vector store"}

    # 4. LLM provider configuration
    if settings.LLM_PROVIDER == "fake":
        checks["llm"] = {"status": "ok"}
    elif settings.LLM_PROVIDER in ("openai", "anthropic"):
        if settings.LLM_API_KEY and settings.LLM_API_KEY.strip():
            checks["llm"] = {"status": "ok"}
        else:
            checks["llm"] = {"status": "error", "detail": "LLM API key not configured"}
    else:
        checks["llm"] = {"status": "error", "detail": "unsupported LLM provider"}

    is_ready = all(check.get("status") == "ok" for check in checks.values())
    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "degraded",
            "checks": checks,
        },
    )

