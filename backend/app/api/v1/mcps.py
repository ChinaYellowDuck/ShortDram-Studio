"""MCP server management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import McpServiceDep
from app.models.mcp import Mcp
from app.schemas.common import PaginatedResponse
from app.schemas.mcp import (
    McpCreate,
    McpResponse,
    McpTestConnectionRequest,
    McpTestConnectionResponse,
    McpUpdate,
)
from app.services.mcp_service import mask_secrets

router = APIRouter()


def to_response(mcp: Mcp) -> dict:
    """Convert an MCP ORM instance to a response dict with masked secrets."""
    return {
        "id": mcp.id,
        "name": mcp.name,
        "url": mcp.url,
        "transport": mcp.transport,
        "mcp_type": mcp.mcp_type,
        "config": mcp.config,
        "secrets": mask_secrets(mcp.secrets),
        "tools": mcp.tools,
        "description": mcp.description,
        "is_enabled": mcp.is_enabled,
        "created_at": mcp.created_at,
        "updated_at": mcp.updated_at,
    }


@router.get("", response_model=PaginatedResponse[McpResponse], summary="获取 MCP 列表")
def list_mcps(
    service: McpServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_enabled: bool | None = None,
    mcp_type: str | None = None,
    search: str | None = None,
):
    mcps, total = service.list_mcps(
        skip=(page - 1) * page_size,
        limit=page_size,
        is_enabled=is_enabled,
        mcp_type=mcp_type,
        search=search,
    )
    return PaginatedResponse(
        items=[to_response(m) for m in mcps],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{mcp_id}", response_model=McpResponse, summary="获取 MCP 详情")
def get_mcp(mcp_id: int, service: McpServiceDep):
    mcp = service.get_by_id_or_404(mcp_id)
    return to_response(mcp)


@router.post("", response_model=McpResponse, status_code=status.HTTP_201_CREATED, summary="创建 MCP")
def create_mcp(data: McpCreate, service: McpServiceDep):
    mcp = service.create(data)
    return to_response(mcp)


@router.put("/{mcp_id}", response_model=McpResponse, summary="更新 MCP")
def update_mcp(mcp_id: int, data: McpUpdate, service: McpServiceDep):
    mcp = service.update(mcp_id, data)
    return to_response(mcp)


@router.delete("/{mcp_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 MCP")
def delete_mcp(mcp_id: int, service: McpServiceDep):
    service.delete(mcp_id)


@router.post(
    "/test-connection",
    response_model=McpTestConnectionResponse,
    summary="测试 MCP 连接",
)
def test_mcp_connection(data: McpTestConnectionRequest, service: McpServiceDep):
    return service.test_connection(
        url=data.url,
        transport=data.transport,
        config=data.config,
        secrets=data.secrets,
    )


@router.post(
    "/{mcp_id}/test-connection",
    response_model=McpTestConnectionResponse,
    summary="测试已有 MCP 的连接",
)
def test_existing_mcp_connection(mcp_id: int, service: McpServiceDep):
    mcp = service.get_by_id_or_404(mcp_id)
    return service.test_connection(
        url=mcp.url,
        transport=mcp.transport,
        config=mcp.config,
        secrets=mcp.secrets,
    )


@router.post("/{mcp_id}/refresh-tools", summary="刷新 MCP 工具列表")
def refresh_mcp_tools(mcp_id: int, service: McpServiceDep):
    tools = service.refresh_tools(mcp_id)
    return {"tools": tools, "count": len(tools)}
