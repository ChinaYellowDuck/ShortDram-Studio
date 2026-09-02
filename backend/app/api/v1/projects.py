"""Project management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import ProjectServiceDep
from app.models.project import ProjectStatus
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProjectResponse], summary="获取项目列表")
def list_projects(
    service: ProjectServiceDep,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: ProjectStatus | None = Query(None, alias="status", description="按状态筛选"),
    search: str | None = Query(None, description="按名称搜索"),
):
    """List projects with pagination, optional status filter and search."""
    skip = (page - 1) * page_size
    projects, total = service.list_projects(
        skip=skip, limit=page_size, status_filter=status_filter, search=search
    )
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectResponse, summary="获取项目详情")
def get_project(project_id: int, service: ProjectServiceDep):
    """Get a specific project by ID."""
    return service.get_by_id_or_404(project_id)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
)
def create_project(project_data: ProjectCreate, service: ProjectServiceDep):
    """Create a new short drama project."""
    return service.create(project_data)


@router.put("/{project_id}", response_model=ProjectResponse, summary="更新项目")
def update_project(project_id: int, project_data: ProjectUpdate, service: ProjectServiceDep):
    """Update an existing project."""
    return service.update(project_id, project_data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除项目")
def delete_project(project_id: int, service: ProjectServiceDep):
    """Delete a project."""
    service.delete(project_id)


@router.patch("/{project_id}/status", response_model=ProjectResponse, summary="更新项目状态")
def update_project_status(
    project_id: int,
    new_status: ProjectStatus,
    service: ProjectServiceDep,
):
    """Update the status of a project."""
    return service.update_status(project_id, new_status)
