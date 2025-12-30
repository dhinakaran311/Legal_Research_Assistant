"""
API Key Middleware - Secure internal communication
Validates requests from backend using INTERNAL_API_KEY
"""
from fastapi import Request, HTTPException, status
from config import settings
import logging

logger = logging.getLogger(__name__)

async def verify_internal_api_key(request: Request, call_next):
    """
    Middleware to verify internal API key from backend
    
    Public endpoints (no auth required):
    - /health
    - /docs
    - /openapi.json
    
    Protected endpoints (require API key):
    - /api/*
    """
    # Allow public endpoints
    public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # Check API key for protected endpoints
    api_key = request.headers.get("X-Internal-API-Key")
    
    if not api_key:
        logger.warning(f"Missing API key for {request.url.path}")
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
        logger.warning(f"Invalid API key attempt for {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # API key valid, proceed
    return await call_next(request)
