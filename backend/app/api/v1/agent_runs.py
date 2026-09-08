"""Agent run records query endpoints."""
from fastapi import APIRouter, status

from app.api.deps import AgentServiceDep
from app.schemas.agent import AgentRunDetailResponse, AgentRunResponse, AgentRunStepResponse
from app.schemas.common import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get(
    "",
    summary="获取智能体运行记录列表",
    response_model=PaginatedResponse[AgentRunResponse],
)
def list_runs(
    service: AgentServiceDep,
    params: PaginationParams,
    agent_id: int | None = None,
    project_id: int | None = None,
    status: str | None = None,
):
    """List agent runs with pagination and filters.

    - **agent_id**: 按智能体筛选
    - **project_id**: 按项目筛选
    - **status**: 按状态筛选 (pending/running/completed/failed/cancelled)
    """
    runs, total = service.list_runs(
        skip=(params.page - 1) * params.page_size,
        limit=params.page_size,
        agent_id=agent_id,
        project_id=project_id,
        status=status,
    )
    return PaginatedResponse(
        items=runs,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=(total + params.page_size - 1) // params.page_size,
    )


@router.get(
    "/{run_id}",
    summary="获取运行记录详情（含步骤）",
    response_model=AgentRunDetailResponse,
)
def get_run_detail(service: AgentServiceDep, run_id: int):
    """Get agent run detail including all steps."""
    run = service.get_run_detail(run_id)
    return AgentRunDetailResponse.model_validate(run)


@router.get(
    "/{run_id}/steps",
    summary="获取运行记录的步骤列表",
    response_model=list[AgentRunStepResponse],
)
def list_run_steps(service: AgentServiceDep, run_id: int):
    """List all steps of an agent run, ordered by step_index."""
    return service.list_steps(run_id)


@router.delete(
    "/{run_id}",
    summary="删除运行记录",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_run(service: AgentServiceDep, run_id: int):
    """Delete an agent run record (cascades to steps)."""
    run = service.get_run_by_id_or_404(run_id)
    service.db.delete(run)
    service.db.commit()
