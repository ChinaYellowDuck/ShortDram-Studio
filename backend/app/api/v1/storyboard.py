"""Storyboard management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import StoryboardServiceDep
from app.schemas.storyboard import (
    ReorderRequest,
    StoryboardShotCreate,
    StoryboardShotResponse,
    StoryboardShotUpdate,
)

router = APIRouter()


@router.get("", summary="获取项目分镜列表")
def list_storyboard_shots(
    project_id: int = Query(..., description="项目 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    service: StoryboardServiceDep = ...,
):
    """List all storyboard shots for a project, ordered by order_index."""
    skip = (page - 1) * page_size
    shots, total = service.list_shots(
        project_id=project_id,
        skip=skip,
        limit=page_size,
    )
    return {
        "items": shots,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{shot_id}", response_model=StoryboardShotResponse, summary="获取分镜详情")
def get_storyboard_shot(shot_id: int, service: StoryboardServiceDep):
    """Get a specific storyboard shot by ID."""
    return service.get_by_id_or_404(shot_id)


@router.post(
    "",
    response_model=StoryboardShotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建分镜",
)
def create_storyboard_shot(
    shot_data: StoryboardShotCreate,
    project_id: int = Query(..., description="项目 ID"),
    service: StoryboardServiceDep = ...,
):
    """Create a new storyboard shot."""
    return service.create(project_id=project_id, shot_data=shot_data)


@router.put("/{shot_id}", response_model=StoryboardShotResponse, summary="更新分镜")
def update_storyboard_shot(
    shot_id: int,
    update_data: StoryboardShotUpdate,
    service: StoryboardServiceDep,
):
    """Update an existing storyboard shot."""
    return service.update(shot_id, update_data)


@router.delete("/{shot_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除分镜")
def delete_storyboard_shot(shot_id: int, service: StoryboardServiceDep):
    """Delete a storyboard shot."""
    service.delete(shot_id)


@router.post("/reorder", summary="重排分镜顺序")
def reorder_storyboard(
    reorder_data: ReorderRequest,
    project_id: int = Query(..., description="项目 ID"),
    service: StoryboardServiceDep = ...,
):
    """Reorder storyboard shots based on provided ID list."""
    return service.reorder(project_id=project_id, shot_ids=reorder_data.shot_ids)
