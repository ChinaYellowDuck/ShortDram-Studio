"""Storyboard related models.

Scene-level granularity: one ScriptScene = one StoryboardShot.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CompositionType(str, enum.Enum):
    """Shot composition / framing."""

    EXTREME_LONG = "大远景"
    LONG = "远景"
    FULL = "全景"
    MEDIUM = "中景"
    MEDIUM_CLOSE = "中近景"
    CLOSE_UP = "近景"
    EXTREME_CLOSE = "特写"


class CameraMovement(str, enum.Enum):
    """Camera movement type."""

    FIXED = "固定"
    PUSH_IN = "推"
    PULL_OUT = "拉"
    PAN = "摇"
    TRACK = "移"
    FOLLOW = "跟"
    ZOOM = "变焦"


class CameraAngle(str, enum.Enum):
    """Camera angle."""

    EYE_LEVEL = "平视"
    LOW_ANGLE = "仰视"
    HIGH_ANGLE = "俯视"
    SIDE = "侧视"
    DUTCH = "倾斜"


class StoryboardShot(BaseModel):
    """A single storyboard shot (scene-level granularity).

    Attributes:
        project_id: Owning project ID.
        script_scene_id: Associated script scene.
        shot_number: Human-readable shot number.
        order_index: Sort order within the project.
        composition: Shot framing type.
        camera_movement: Camera movement type.
        camera_angle: Camera angle.
        visual_description: Detailed visual prompt for video generation.
        duration_seconds: Estimated duration.
        key_frame_url: Key frame preview image.
        character_ids: JSON array of character asset IDs in this shot.
        prop_ids: JSON array of prop asset IDs in this shot.
    """

    __tablename__ = "storyboard_shots"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_scene_id: Mapped[int] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    composition: Mapped[CompositionType] = mapped_column(
        Enum(CompositionType, values_callable=lambda x: [e.value for e in x]),
        default=CompositionType.MEDIUM,
        nullable=False,
    )
    camera_movement: Mapped[CameraMovement] = mapped_column(
        Enum(CameraMovement, values_callable=lambda x: [e.value for e in x]),
        default=CameraMovement.FIXED,
        nullable=False,
    )
    camera_angle: Mapped[CameraAngle] = mapped_column(
        Enum(CameraAngle, values_callable=lambda x: [e.value for e in x]),
        default=CameraAngle.EYE_LEVEL,
        nullable=False,
    )
    visual_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    key_frame_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    character_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    prop_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<StoryboardShot(id={self.id}, shot_number='{self.shot_number}')>"
