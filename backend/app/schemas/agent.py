"""Pydantic schemas for agents and agent runs."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ── Agent Metadata ────────────────────────────────────────────────────────────


class AgentBase(BaseModel):
    """Base schema for agent metadata."""

    agent_key: str = Field(
        ..., min_length=1, max_length=50, description="Business-unique agent key"
    )
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=500, description="Agent description")
    agent_type: str = Field(..., max_length=50, description="Agent type/category")
    category: Optional[str] = Field(None, max_length=50, description="Display category")
    is_enabled: bool = Field(True, description="Whether the agent is enabled")
    default_llm_config_id: Optional[int] = Field(None, description="Default LLM config ID")
    default_params: Optional[Dict[str, Any]] = Field(None, description="Default parameters JSON")
    version: str = Field("1.0", max_length=20, description="Agent version")


class AgentCreate(AgentBase):
    """Schema for creating an agent."""

    pass


class AgentUpdate(BaseModel):
    """Schema for updating an agent (all fields optional)."""

    agent_key: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    agent_type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    is_enabled: Optional[bool] = None
    default_llm_config_id: Optional[int] = None
    default_params: Optional[Dict[str, Any]] = None
    version: Optional[str] = Field(None, max_length=20)


class AgentResponse(AgentBase):
    """Schema for agent response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Run Steps ──────────────────────────────────────────────────────────


class AgentRunStepBase(BaseModel):
    """Base schema for an agent run step (graph node execution)."""

    step_name: str = Field(..., max_length=100, description="LangGraph node name")
    step_index: int = Field(0, description="Sequential step index (for looped nodes)")
    status: str = Field("pending", max_length=20, description="Step status")
    input_summary: Optional[str] = Field(None, description="Truncated input summary")
    output_summary: Optional[str] = Field(None, description="Truncated output summary")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Token consumption")


class AgentRunStepCreate(AgentRunStepBase):
    """Schema for creating a run step."""

    pass


class AgentRunStepUpdate(BaseModel):
    """Schema for updating a run step."""

    status: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class AgentRunStepResponse(AgentRunStepBase):
    """Schema for run step response."""

    id: int
    run_id: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Agent Runs ───────────────────────────────────────────────────────────────


class AgentRunBase(BaseModel):
    """Base schema for an agent run."""

    agent_id: Optional[int] = Field(None, description="Agent metadata ID")
    project_id: Optional[int] = Field(None, description="Project ID")
    status: str = Field("pending", max_length=20, description="Run status")
    llm_config_id: Optional[int] = Field(None, description="LLM config used")
    llm_model_name: Optional[str] = Field(None, max_length=100, description="Model name snapshot")
    input_summary: Optional[str] = Field(None, description="Truncated input summary")
    output_summary: Optional[str] = Field(None, description="Truncated output summary")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: Optional[int] = Field(None, description="Total duration in milliseconds")
    total_tokens: Optional[int] = Field(None, description="Total token consumption")


class AgentRunCreate(AgentRunBase):
    """Schema for creating an agent run."""

    pass


class AgentRunUpdate(BaseModel):
    """Schema for updating an agent run."""

    status: Optional[str] = None
    llm_config_id: Optional[int] = None
    llm_model_name: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    total_tokens: Optional[int] = None
    project_id: Optional[int] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class AgentRunResponse(AgentRunBase):
    """Schema for agent run response (without steps)."""

    id: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRunDetailResponse(AgentRunResponse):
    """Schema for agent run detail response (includes steps)."""

    steps: list[AgentRunStepResponse] = Field(default_factory=list)
