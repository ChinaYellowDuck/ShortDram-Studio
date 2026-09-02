"""Pydantic schemas for LLM configuration."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LLMConfigBase(BaseModel):
    """Base schema for LLM configuration."""

    name: str = Field(..., min_length=1, max_length=100, description="Configuration display name")
    provider: str = Field(..., min_length=1, max_length=50, description="LLM provider type")
    model_name: str = Field(..., min_length=1, max_length=100, description="Model name/identifier")
    base_url: Optional[str] = Field(None, max_length=500, description="Custom API base URL")
    description: Optional[str] = Field(None, max_length=500, description="Configuration description")


class LLMConfigCreate(LLMConfigBase):
    """Schema for creating an LLM configuration."""

    api_key: str = Field(..., min_length=1, description="API key (will be encrypted)")
    is_default: bool = Field(False, description="Set as default configuration")


class LLMConfigUpdate(BaseModel):
    """Schema for updating an LLM configuration.

    All fields are optional — only provided fields will be updated.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = Field(None, min_length=1, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_key: Optional[str] = Field(None, min_length=1, description="New API key (will be encrypted)")
    base_url: Optional[str] = Field(None, max_length=500)
    is_default: Optional[bool] = Field(None, description="Set as default configuration")
    description: Optional[str] = Field(None, max_length=500)


class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response.

    Note: api_key is never returned in the response for security reasons.
    """

    id: int
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LLMProviderInfo(BaseModel):
    """Information about a supported LLM provider."""

    key: str = Field(description="Provider identifier key")
    name: str = Field(description="Human-readable provider name")
    default_model: str = Field(description="Default model name for this provider")
    supports_base_url: bool = Field(description="Whether custom base URL is supported")


class LLMTestResult(BaseModel):
    """Result of testing an LLM configuration."""

    success: bool = Field(description="Whether the test was successful")
    message: str = Field(description="Result message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    model: Optional[str] = Field(None, description="Model that responded")
