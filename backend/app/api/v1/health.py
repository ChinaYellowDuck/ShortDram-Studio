"""Health check endpoints."""
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("", summary="服务健康检查")
async def health_check():
    """Check if the API service is running properly."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "env": settings.APP_ENV,
    }


@router.get("/langsmith", summary="LangSmith 状态检查")
async def langsmith_status():
    """Check LangSmith tracing configuration status."""
    return {
        "enabled": settings.LANGCHAIN_TRACING_V2,
        "project": settings.LANGCHAIN_PROJECT if settings.LANGCHAIN_TRACING_V2 else None,
        "endpoint": settings.LANGCHAIN_ENDPOINT if settings.LANGCHAIN_TRACING_V2 else None,
    }
