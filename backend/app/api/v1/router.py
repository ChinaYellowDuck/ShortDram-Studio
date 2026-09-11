"""API v1 router - aggregates all v1 route modules."""
from fastapi import APIRouter

from app.api.v1 import agents as agents_router
from app.api.v1 import agent_runs as agent_runs_router
from app.api.v1 import agents_meta as agents_meta_router
from app.api.v1 import assets as assets_router
from app.api.v1 import health as health_router
from app.api.v1 import llm_configs as llm_configs_router
from app.api.v1 import mcps as mcps_router
from app.api.v1 import projects as projects_router
from app.api.v1 import scripts as scripts_router
from app.api.v1 import skills as skills_router
from app.api.v1 import storyboard as storyboard_router

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(health_router.router, prefix="/health", tags=["health"])
api_router.include_router(llm_configs_router.router, prefix="/llm-configs", tags=["LLM 配置"])
api_router.include_router(mcps_router.router, prefix="/mcps", tags=["MCP 管理"])
api_router.include_router(skills_router.router, prefix="/skills", tags=["Skill 管理"])
api_router.include_router(projects_router.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(assets_router.router, prefix="/assets", tags=["资产管理"])
api_router.include_router(storyboard_router.router, prefix="/storyboard", tags=["分镜管理"])
api_router.include_router(scripts_router.router, prefix="/scripts", tags=["剧本管理"])
api_router.include_router(agents_meta_router.router, prefix="/agents/meta", tags=["智能体管理"])
api_router.include_router(agent_runs_router.router, prefix="/agent-runs", tags=["智能体运行记录"])
api_router.include_router(agents_router.router, prefix="/agents", tags=["智能体"])
