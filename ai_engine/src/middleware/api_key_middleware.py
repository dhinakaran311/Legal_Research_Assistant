"""
API Key Middleware - Secure internal communication
Validates requests from backend using INTERNAL_API_KEY
"""
from fastapi import Request, HTTPException, status, Header
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


async def verify_internal_api_key(request: Request, call_next):
    """
    HTTP Middleware to verify internal API key.
    Public endpoints (no auth): /, /health, /docs, /openapi.json, /redoc
    Protected: /api/*
    """
    public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    if request.url.path == "/" or any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)

    api_key = request.headers.get("X-Internal-API-Key")

    if not api_key:
        logger.warning("Missing API key for %s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-API-Key header"
        )

    if not settings.INTERNAL_API_KEY:
        logger.error("INTERNAL_API_KEY not configured in AI Engine!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )

    if api_key != settings.INTERNAL_API_KEY:
        logger.warning("Invalid API key attempt for %s", request.url.path)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return await call_next(request)


async def require_api_key(x_internal_api_key: Optional[str] = Header(default=None)):
    """
    FastAPI Depends-compatible API key check.
    Use this on individual routes instead of the HTTP middleware version.
    """
    if not x_internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-API-Key header"
        )
    if not settings.INTERNAL_API_KEY or x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
