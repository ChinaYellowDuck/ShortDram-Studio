"""Pydantic schemas for MCP servers."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class McpBase(BaseModel):
    """Base schema for an MCP server."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    url: str = Field(..., min_length=1, max_length=500, description="Server endpoint")
    transport: str = Field("streamable_http", max_length=50, description="Transport type")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional JSON configuration")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_enabled: bool = Field(True, description="Whether the MCP server is enabled")


class McpCreate(McpBase):
    """Schema for creating an MCP server."""

    pass


class McpUpdate(BaseModel):
    """Schema for updating an MCP server (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    transport: Optional[str] = Field(None, max_length=50)
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None


class McpResponse(McpBase):
    """Schema for an MCP server response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
