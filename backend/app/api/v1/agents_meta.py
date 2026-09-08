"""Agent metadata management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import AgentServiceDep
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", summary="获取智能体列表", response_model=PaginatedResponse[AgentResponse])
def list_agents(
    service: AgentServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    agent_type: str | None = None,
    is_enabled: bool | None = None,
    search: str | None = None,
):
    """List agents with pagination and filters.

    - **agent_type**: 按智能体类型筛选
    - **is_enabled**: 按启用状态筛选
    - **search**: 按名称/描述/key 搜索
    """
    agents, total = service.list_agents(
        skip=(page - 1) * page_size,
        limit=page_size,
        agent_type=agent_type,
        is_enabled=is_enabled,
        search=search,
    )
    return PaginatedResponse(
        items=agents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{agent_id}", summary="获取智能体详情", response_model=AgentResponse)
def get_agent(service: AgentServiceDep, agent_id: int):
    """Get agent details by ID."""
    return service.get_by_id_or_404(agent_id)


@router.post(
    "",
    summary="创建智能体",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent(service: AgentServiceDep, data: AgentCreate):
    """Create a new agent."""
    return service.create(data)


@router.put("/{agent_id}", summary="更新智能体", response_model=AgentResponse)
def update_agent(service: AgentServiceDep, agent_id: int, data: AgentUpdate):
    """Update an existing agent."""
    return service.update(agent_id, data)


@router.delete("/{agent_id}", summary="删除智能体", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(service: AgentServiceDep, agent_id: int):
    """Delete an agent."""
    service.delete(agent_id)


@router.patch(
    "/{agent_id}/enabled",
    summary="启用/禁用智能体",
    response_model=AgentResponse,
)
def set_agent_enabled(service: AgentServiceDep, agent_id: int, enabled: bool):
    """Enable or disable an agent.

    - **enabled**: true=启用, false=禁用
    """
    return service.set_enabled(agent_id, enabled)
