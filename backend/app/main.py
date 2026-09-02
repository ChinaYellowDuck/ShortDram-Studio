"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    setup_logger(settings.LOG_LEVEL)
    logger = setup_logger()
    logger.info(f"Starting {settings.APP_NAME} v{__import__('app').__version__}")
    logger.info(f"Environment: {settings.APP_ENV}")
    if settings.LANGCHAIN_TRACING_V2:
        logger.info("LangSmith tracing is enabled")

    yield

    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Multi-Agent Short Drama Production Platform",
        version="0.1.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


@app.get("/", tags=["root"], summary="Root endpoint")
async def root():
    """Root endpoint returning basic application info."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
