"""LLM configuration management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import LLMConfigServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigUpdate,
    LLMProviderInfo,
    LLMTestResult,
)

router = APIRouter()


@router.get("/providers", response_model=list[LLMProviderInfo], summary="获取支持的 LLM 提供商列表")
def get_supported_providers(service: LLMConfigServiceDep):
    """Get all supported LLM providers."""
    return service.get_supported_providers()


@router.get("", response_model=PaginatedResponse[LLMConfigResponse], summary="获取 LLM 配置列表")
def list_configs(
    service: LLMConfigServiceDep,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """List all LLM configurations with pagination."""
    skip = (page - 1) * page_size
    configs, total = service.list_configs(skip=skip, limit=page_size)
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=configs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/default", response_model=LLMConfigResponse, summary="获取默认 LLM 配置")
def get_default_config(service: LLMConfigServiceDep):
    """Get the default LLM configuration."""
    return service.get_default_or_404()


@router.get("/{config_id}", response_model=LLMConfigResponse, summary="获取单个 LLM 配置详情")
def get_config(config_id: int, service: LLMConfigServiceDep):
    """Get a specific LLM configuration by ID."""
    return service.get_by_id_or_404(config_id)


@router.post(
    "",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建 LLM 配置",
)
def create_config(config_data: LLMConfigCreate, service: LLMConfigServiceDep):
    """Create a new LLM configuration.

    The API key will be encrypted before storage.
    """
    return service.create(config_data)


@router.put("/{config_id}", response_model=LLMConfigResponse, summary="更新 LLM 配置")
def update_config(config_id: int, config_data: LLMConfigUpdate, service: LLMConfigServiceDep):
    """Update an existing LLM configuration."""
    return service.update(config_id, config_data)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 LLM 配置")
def delete_config(config_id: int, service: LLMConfigServiceDep):
    """Delete an LLM configuration."""
    service.delete(config_id)


@router.post("/{config_id}/set-default", response_model=LLMConfigResponse, summary="设为默认配置")
def set_default_config(config_id: int, service: LLMConfigServiceDep):
    """Set a configuration as the default."""
    return service.set_default(config_id)


@router.post("/{config_id}/test", response_model=LLMTestResult, summary="测试 LLM 配置连通性")
async def test_config(config_id: int, service: LLMConfigServiceDep):
    """Test an LLM configuration by making a simple API call."""
    return await service.test_config(config_id)
