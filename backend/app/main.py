"""Main FastAPI application factory for CivicShield NG."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.database import get_db
from backend.app.core.rate_limit import rate_limiter, RATE_LIMIT_POLICIES
from backend.app.core.exceptions import (
    CivicShieldException,
    civicshield_exception_handler,
    generic_exception_handler,
)
from backend.app.common.schemas import APIResponse
from backend.app.modules.auth.router import router as auth_router
from backend.app.modules.reporting.router import router as reporting_router
from backend.app.modules.registry.router import router as registry_router
from backend.app.modules.ai_engine.router import router as ai_router
from backend.app.modules.verification.router import router as verification_router
from backend.app.modules.notifications.router import router as notifications_router
from backend.app.modules.narratives.router import router as narratives_router
from backend.app.modules.security_audit.router import router as security_router
from backend.app.modules.ai_engine.voice import router as voice_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.PROJECT_VERSION} [{settings.ENVIRONMENT}]")

    # Ensure upload directory exists securely
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Media upload directory verified at: {settings.UPLOAD_DIR.resolve()}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    """Enforce defense-in-depth rate limits and inject hardened HTTP security headers."""
    # 1. Rate Limiting Check on Sensitive Endpoints
    client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path
    if path in RATE_LIMIT_POLICIES and request.method == "POST":
        limit, window = RATE_LIMIT_POLICIES[path]
        allowed, retry_after = rate_limiter.is_allowed(client_ip, limit=limit, window_seconds=window)
        if not allowed:
            logger.warning(f"Rate limit exceeded on '{path}' for IP {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "data": None,
                    "message": f"Rate limit exceeded for endpoint '{path}'. Please retry after {retry_after}s.",
                    "errors": [f"Too many requests from this IP address. Window: {window}s."],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                headers={"Retry-After": str(retry_after)},
            )

    response = await call_next(request)

    # 2. Hardened Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Exception handlers
app.add_exception_handler(CivicShieldException, civicshield_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(reporting_router, prefix=settings.API_V1_STR)
app.include_router(registry_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(narratives_router, prefix=settings.API_V1_STR)
app.include_router(security_router, prefix=settings.API_V1_STR)
app.include_router(voice_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root() -> APIResponse[dict]:
    """Root endpoint presenting platform metadata."""
    return APIResponse(
        data={
            "platform": settings.PROJECT_NAME,
            "version": settings.PROJECT_VERSION,
            "description": settings.PROJECT_DESCRIPTION,
            "docs": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
        },
        message="CivicShield NG API is operational.",
    )


@app.get("/health", tags=["Health"], include_in_schema=False)
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> APIResponse[dict]:
    """Verify application and database health status."""
    try:
        # Parameterized query to verify database connectivity
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        db_status = "unhealthy"

    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "version": settings.PROJECT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return APIResponse(
        data=health_data,
        message="System health check completed successfully.",
    )
