"""Asset management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import AssetServiceDep
from app.models.asset import AssetType
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter()


@router.get("", summary="获取项目资产列表")
def list_assets(
    project_id: int = Query(..., description="项目 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type_filter: AssetType | None = Query(None, alias="type", description="按类型筛选"),
    search: str | None = Query(None, description="按名称搜索"),
    service: AssetServiceDep = ...,
):
    """List assets for a project with filtering and pagination."""
    skip = (page - 1) * page_size
    assets, total = service.list_assets(
        project_id=project_id,
        skip=skip,
        limit=page_size,
        asset_type=type_filter,
        search=search,
    )
    return {
        "items": assets,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{asset_id}", response_model=AssetResponse, summary="获取资产详情")
def get_asset(asset_id: int, service: AssetServiceDep):
    """Get a specific asset by ID."""
    return service.get_by_id_or_404(asset_id)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建资产",
)
def create_asset(
    asset_data: AssetCreate,
    project_id: int = Query(..., description="项目 ID"),
    service: AssetServiceDep = ...,
):
    """Create a new asset for a project."""
    return service.create(project_id=project_id, asset_data=asset_data)


@router.put("/{asset_id}", response_model=AssetResponse, summary="更新资产")
def update_asset(
    asset_id: int,
    update_data: AssetUpdate,
    service: AssetServiceDep,
):
    """Update an existing asset."""
    return service.update(asset_id, update_data)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除资产")
def delete_asset(asset_id: int, service: AssetServiceDep):
    """Delete an asset."""
    service.delete(asset_id)
