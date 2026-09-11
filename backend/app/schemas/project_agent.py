"""Pydantic schemas for project agent configuration."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectAgentConfigBase(BaseModel):
    """Base schema for project agent config."""

    is_enabled: bool = Field(default=True, description="是否启用")
    is_director: bool = Field(default=False, description="是否为总控智能体")
    llm_config_id: Optional[int] = Field(None, description="使用的LLM配置ID（覆盖默认）")
    params_override: Optional[dict] = Field(None, description="参数覆盖（JSON）")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度（覆盖默认）")
    system_message_override: Optional[str] = Field(None, description="系统提示词（覆盖默认）")
    priority: int = Field(default=100, description="优先级（数字越小越优先）")
    role_description: Optional[str] = Field(None, max_length=500, description="在本项目中的角色描述")


class ProjectAgentConfigCreate(ProjectAgentConfigBase):
    """Schema for creating a project agent config."""

    agent_id: int = Field(..., description="智能体ID")


class ProjectAgentConfigUpdate(BaseModel):
    """Schema for updating a project agent config."""

    is_enabled: Optional[bool] = None
    is_director: Optional[bool] = None
    llm_config_id: Optional[int] = None
    params_override: Optional[dict] = None
    temperature: Optional[float] = None
    system_message_override: Optional[str] = None
    priority: Optional[int] = None
    role_description: Optional[str] = None


class ProjectAgentConfigResponse(ProjectAgentConfigBase):
    """Schema for project agent config response."""

    id: int
    project_id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime
    # Agent info (joined)
    agent_key: Optional[str] = None
    agent_name: Optional[str] = None
    agent_description: Optional[str] = None
    agent_type: Optional[str] = None
    agent_category: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectAgentSetupRequest(BaseModel):
    """Request for batch-setting up agents for a project.

    Sets the director agent and select which sub-agents are enabled.
    """

    director_agent_id: int = Field(..., description="总控智能体ID")
    enabled_agent_ids: list[int] = Field(
        default_factory=(), description="启用的子智能体ID列表（包含总控）"
    )


class AgentSimpleResponse(BaseModel):
    """Schema for agent metadata (list view)."""

    id: int
    agent_key: str
    name: str
    description: Optional[str] = None
    agent_type: str
    category: Optional[str] = None
    is_enabled: bool
    temperature: float
    version: str

    model_config = {"from_attributes": True}
