"""Pydantic schemas for MCP servers."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class McpBase(BaseModel):
    """Base schema for an MCP server."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    url: str = Field(..., min_length=1, max_length=500, description="Server endpoint")
    transport: str = Field("streamable_http", max_length=50, description="Transport type")
    mcp_type: str = Field("custom", max_length=30, description="Server type: official/third_party/custom")
    config: Optional[Dict[str, Any]] = Field(None, description="Public JSON configuration")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    is_enabled: bool = Field(True, description="Whether the MCP server is enabled")


class McpCreate(McpBase):
    """Schema for creating an MCP server."""

    secrets: Optional[Dict[str, Any]] = Field(None, description="Sensitive configuration (api keys, tokens)")


class McpUpdate(BaseModel):
    """Schema for updating an MCP server (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    transport: Optional[str] = Field(None, max_length=50)
    mcp_type: Optional[str] = Field(None, max_length=30)
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, Any]] = None
    description: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None


class McpResponse(BaseModel):
    """Schema for an MCP server response (secrets masked)."""

    id: int
    name: str
    url: str
    transport: str
    mcp_type: str
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, Any]] = Field(
        None,
        description="Masked secrets - values show '***' if set, key names are preserved",
    )
    tools: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class McpTestConnectionRequest(BaseModel):
    """Schema for testing MCP server connection."""

    url: str = Field(..., min_length=1, max_length=500)
    transport: str = Field("streamable_http", max_length=50)
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, Any]] = None


class McpTestConnectionResponse(BaseModel):
    """Schema for MCP test connection result."""

    ok: bool
    error: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    server_version: Optional[str] = None
    latency_ms: Optional[float] = None


class McpTool(BaseModel):
    """Schema for an MCP tool."""

    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
