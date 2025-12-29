"""
AI Engine Main Application
FastAPI-based microservice for legal AI processing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from routes import query

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    """
    # Startup
    logger.info("🚀 AI Engine starting up...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Running on {settings.API_HOST}:{settings.API_PORT}")
    
    yield
    
    # Shutdown
    logger.info("🛑 AI Engine shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Legal AI Engine",
    description="AI microservice for legal research and retrieval",
    version="2.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Legal AI Engine",
        "version": "2.1.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns the health status of the AI engine
    """
    return {
        "status": "healthy",
        "service": "ai-engine",
        "version": "2.1.0",
        "environment": "development" if settings.DEBUG else "production"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
