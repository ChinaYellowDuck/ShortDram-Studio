"""MCP server management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import McpServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.mcp import McpCreate, McpResponse, McpUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[McpResponse], summary="获取 MCP 列表")
def list_mcps(
    service: McpServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_enabled: bool | None = None,
    search: str | None = None,
):
    mcps, total = service.list_mcps(
        skip=(page - 1) * page_size,
        limit=page_size,
        is_enabled=is_enabled,
        search=search,
    )
    return PaginatedResponse(
        items=mcps,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{mcp_id}", response_model=McpResponse, summary="获取 MCP 详情")
def get_mcp(mcp_id: int, service: McpServiceDep):
    return service.get_by_id_or_404(mcp_id)


@router.post("", response_model=McpResponse, status_code=status.HTTP_201_CREATED, summary="创建 MCP")
def create_mcp(data: McpCreate, service: McpServiceDep):
    return service.create(data)


@router.put("/{mcp_id}", response_model=McpResponse, summary="更新 MCP")
def update_mcp(mcp_id: int, data: McpUpdate, service: McpServiceDep):
    return service.update(mcp_id, data)


@router.delete("/{mcp_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 MCP")
def delete_mcp(mcp_id: int, service: McpServiceDep):
    service.delete(mcp_id)
