"""Pydantic schemas for Asset."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.asset import AssetType, AssetSource


class AssetBase(BaseModel):
    type: AssetType = Field(..., description="资产类型: character/scene/prop")
    name: str = Field(..., min_length=1, max_length=200, description="资产名称")
    description: Optional[str] = Field(None, description="详细描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片 URL")
    extra: Optional[dict] = Field(None, description="类型扩展字段 (角色年龄/场景氛围等)")


class AssetCreate(AssetBase):
    source: AssetSource = Field(default=AssetSource.MANUAL, description="来源")


class AssetUpdate(BaseModel):
    type: Optional[AssetType] = Field(None)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None, max_length=500)
    extra: Optional[dict] = Field(None)
    source: Optional[AssetSource] = Field(None)


class AssetResponse(AssetBase):
    id: int
    source: AssetSource
    reference_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
