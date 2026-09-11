"""Pydantic schemas for Storyboard."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.storyboard import CameraAngle, CameraMovement, CompositionType


class StoryboardShotBase(BaseModel):
    script_scene_id: int = Field(..., description="关联剧本场景 ID")
    shot_number: str = Field(..., max_length=50, description="镜头编号")
    order_index: int = Field(default=0, description="排序")
    composition: CompositionType = Field(default=CompositionType.MEDIUM, description="景别")
    camera_movement: CameraMovement = Field(default=CameraMovement.FIXED, description="运镜")
    camera_angle: CameraAngle = Field(default=CameraAngle.EYE_LEVEL, description="角度")
    visual_description: Optional[str] = Field(None, description="画面描述")
    duration_seconds: int = Field(default=5, ge=1, le=300, description="预估时长(秒)")
    key_frame_url: Optional[str] = Field(None, max_length=500, description="关键帧图")
    character_ids: Optional[list[int]] = Field(None, description="出场人物资产ID")
    prop_ids: Optional[list[int]] = Field(None, description="道具资产ID")


class StoryboardShotCreate(StoryboardShotBase):
    pass


class StoryboardShotUpdate(BaseModel):
    script_scene_id: Optional[int] = None
    shot_number: Optional[str] = Field(None, max_length=50)
    order_index: Optional[int] = None
    composition: Optional[CompositionType] = None
    camera_movement: Optional[CameraMovement] = None
    camera_angle: Optional[CameraAngle] = None
    visual_description: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=1, le=300)
    key_frame_url: Optional[str] = Field(None, max_length=500)
    character_ids: Optional[list[int]] = None
    prop_ids: Optional[list[int]] = None


class StoryboardShotResponse(StoryboardShotBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderRequest(BaseModel):
    shot_ids: list[int] = Field(..., description="排序后的镜头ID列表")
