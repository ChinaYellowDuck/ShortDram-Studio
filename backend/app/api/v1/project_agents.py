"""Project Agent Configuration endpoints.

Manages per-project agent setup: which agents are enabled,
which is the director, and per-project parameter overrides.
"""
from fastapi import APIRouter, status

from app.api.deps import ProjectAgentServiceDep
from app.schemas.project_agent import (
    AgentSimpleResponse,
    ProjectAgentConfigCreate,
    ProjectAgentConfigResponse,
    ProjectAgentConfigUpdate,
    ProjectAgentSetupRequest,
)

router = APIRouter()


# ── Available agents (global registry) ─────────────────────────────────────


@router.get("/agents", response_model=list[AgentSimpleResponse], summary="获取可用智能体列表")
def list_available_agents(service: ProjectAgentServiceDep):
    """List all available agents in the registry."""
    return service.list_available_agents()


# ── Project agent configs ──────────────────────────────────────────────────


@router.get(
    "/projects/{project_id}/agents",
    response_model=list[ProjectAgentConfigResponse],
    summary="获取项目的智能体配置列表",
)
def list_project_agents(project_id: int, service: ProjectAgentServiceDep):
    """List all agent configurations for a project."""
    configs = service.list_configs(project_id)
    result = []
    for cfg in configs:
        data = _config_to_response(cfg)
        result.append(data)
    return result


@router.get(
    "/projects/{project_id}/agents/enabled",
    response_model=list[ProjectAgentConfigResponse],
    summary="获取项目已启用的智能体",
)
def list_enabled_project_agents(project_id: int, service: ProjectAgentServiceDep):
    """List enabled agents for a project."""
    configs = service.list_enabled(project_id)
    return [_config_to_response(cfg) for cfg in configs]


@router.get(
    "/projects/{project_id}/agents/director",
    response_model=ProjectAgentConfigResponse,
    summary="获取项目总控智能体",
)
def get_director(project_id: int, service: ProjectAgentServiceDep):
    """Get the director agent for a project."""
    cfg = service.get_director(project_id)
    if not cfg:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No director agent set for this project")
    return _config_to_response(cfg)


@router.post(
    "/projects/{project_id}/agents",
    response_model=ProjectAgentConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="为项目添加智能体",
)
def add_agent_to_project(
    project_id: int,
    data: ProjectAgentConfigCreate,
    service: ProjectAgentServiceDep,
):
    """Add an agent to a project."""
    cfg = service.add_agent(project_id, data)
    return _config_to_response(cfg)


@router.put(
    "/projects/{project_id}/agents/{agent_id}",
    response_model=ProjectAgentConfigResponse,
    summary="更新项目智能体配置",
)
def update_project_agent(
    project_id: int,
    agent_id: int,
    data: ProjectAgentConfigUpdate,
    service: ProjectAgentServiceDep,
):
    """Update an agent config for a project."""
    cfg = service.update_config(project_id, agent_id, data)
    return _config_to_response(cfg)


@router.delete(
    "/projects/{project_id}/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="移除项目中的智能体",
)
def remove_agent_from_project(
    project_id: int,
    agent_id: int,
    service: ProjectAgentServiceDep,
):
    """Remove an agent from a project."""
    service.remove_agent(project_id, agent_id)


@router.post(
    "/projects/{project_id}/agents/{agent_id}/toggle",
    response_model=ProjectAgentConfigResponse,
    summary="切换智能体启用状态",
)
def toggle_agent(
    project_id: int,
    agent_id: int,
    service: ProjectAgentServiceDep,
):
    """Toggle an agent's enabled status."""
    cfg = service.toggle_agent(project_id, agent_id)
    return _config_to_response(cfg)


@router.post(
    "/projects/{project_id}/agents/setup",
    response_model=list[ProjectAgentConfigResponse],
    summary="批量配置项目智能体",
)
def setup_project_agents(
    project_id: int,
    data: ProjectAgentSetupRequest,
    service: ProjectAgentServiceDep,
):
    """Batch setup agents for a project (set director + enabled list)."""
    configs = service.setup_project_agents(project_id, data)
    return [_config_to_response(cfg) for cfg in configs]


# ── Helpers ────────────────────────────────────────────────────────────────


def _config_to_response(cfg) -> dict:
    """Convert a ProjectAgentConfig to a response dict with agent info."""
    agent = cfg.agent
    return {
        "id": cfg.id,
        "project_id": cfg.project_id,
        "agent_id": cfg.agent_id,
        "is_enabled": cfg.is_enabled,
        "is_director": cfg.is_director,
        "llm_config_id": cfg.llm_config_id,
        "params_override": cfg.params_override,
        "temperature": cfg.temperature,
        "system_message_override": cfg.system_message_override,
        "priority": cfg.priority,
        "role_description": cfg.role_description,
        "created_at": cfg.created_at,
        "updated_at": cfg.updated_at,
        "agent_key": agent.agent_key if agent else None,
        "agent_name": agent.name if agent else None,
        "agent_description": agent.description if agent else None,
        "agent_type": agent.agent_type if agent else None,
        "agent_category": agent.category if agent else None,
    }
