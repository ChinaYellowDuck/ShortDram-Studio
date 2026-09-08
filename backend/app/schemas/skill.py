"""Pydantic schemas for skills."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Base schema for a skill."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    content: str = Field(..., min_length=1, description="Instructions/prompt content")
    is_enabled: bool = Field(True, description="Whether the skill is enabled")


class SkillCreate(SkillBase):
    """Schema for creating a skill."""

    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    is_enabled: Optional[bool] = None


class SkillResponse(SkillBase):
    """Schema for a skill response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
