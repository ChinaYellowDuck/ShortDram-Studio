"""Pydantic schemas for Project."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base schema for a project."""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    cover_image: Optional[str] = Field(None, max_length=500, description="Cover image URL/path")


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    status: ProjectStatus = Field(default=ProjectStatus.DRAFT, description="Initial project status")


class ProjectUpdate(BaseModel):
    """Schema for updating a project.

    All fields are optional — only provided fields will be updated.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    status: Optional[ProjectStatus] = Field(None)
    cover_image: Optional[str] = Field(None, max_length=500)


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
