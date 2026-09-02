"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import DBSession
from app.config import settings

router = APIRouter()


@router.get("", summary="服务健康检查")
async def health_check(db: DBSession):
    """Check if the API service and its dependencies are running properly."""
    # Check database connectivity
    db_status = "healthy"
    db_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Check Redis connectivity
    redis_status = "unknown"
    redis_error = None
    try:
        from app.utils.redis import redis_ping

        if await redis_ping():
            redis_status = "healthy"
        else:
            redis_status = "unhealthy"
    except Exception as e:
        redis_status = "unhealthy"
        redis_error = str(e)

    overall_status = "healthy" if db_status == "healthy" and redis_status != "unhealthy" else "degraded"

    return {
        "status": overall_status,
        "version": "0.1.0",
        "env": settings.APP_ENV,
        "services": {
            "database": {
                "status": db_status,
                "error": db_error,
            },
            "redis": {
                "status": redis_status,
                "error": redis_error,
            },
        },
    }


@router.get("/langsmith", summary="LangSmith 状态检查")
async def langsmith_status():
    """Check LangSmith tracing configuration status."""
    return {
        "enabled": settings.LANGCHAIN_TRACING_V2,
        "project": settings.LANGCHAIN_PROJECT if settings.LANGCHAIN_TRACING_V2 else None,
        "endpoint": settings.LANGCHAIN_ENDPOINT if settings.LANGCHAIN_TRACING_V2 else None,
    }
