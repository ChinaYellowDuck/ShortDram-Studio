"""API v1 router - aggregates all v1 route modules."""
from fastapi import APIRouter

from app.api.v1 import agents as agents_router
from app.api.v1 import health as health_router
from app.api.v1 import llm_configs as llm_configs_router
from app.api.v1 import projects as projects_router
from app.api.v1 import scripts as scripts_router

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(health_router.router, prefix="/health", tags=["health"])
api_router.include_router(llm_configs_router.router, prefix="/llm-configs", tags=["LLM 配置"])
api_router.include_router(projects_router.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(scripts_router.router, prefix="/scripts", tags=["剧本管理"])
api_router.include_router(agents_router.router, prefix="/agents", tags=["智能体"])
