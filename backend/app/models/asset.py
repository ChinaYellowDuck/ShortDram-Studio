"""Asset related models.

Three asset types: character, scene, prop.
All assets belong to a project and can be referenced by storyboard shots.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AssetType(str, enum.Enum):
    """Type of asset."""

    CHARACTER = "character"
    SCENE = "scene"
    PROP = "prop"


class AssetSource(str, enum.Enum):
    """Source of the asset."""

    AI_EXTRACTED = "ai_extracted"
    MANUAL = "manual"


class Asset(BaseModel):
    """Production asset for a project.

    Attributes:
        project_id: Owning project ID.
        type: character / scene / prop.
        name: Asset display name.
        description: Detailed description for AI generation.
        image_url: Reference image URL/path.
        extra: Type-specific fields as JSON (character age/gender, scene atmosphere, etc.).
        source: How the asset was created.
        reference_count: Number of references across the project.
    """

    __tablename__ = "assets"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extra: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    source: Mapped[AssetSource] = mapped_column(
        Enum(AssetSource, values_callable=lambda x: [e.value for e in x]),
        default=AssetSource.MANUAL,
        nullable=False,
    )
    reference_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.type}')>"


class AssetScriptMapping(BaseModel):
    """Mapping between assets and script scenes.

    Tracks where each asset appears in the script.
    """

    __tablename__ = "asset_script_mappings"

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_scene_id: Mapped[int | None] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role: Mapped[str | None] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<AssetScriptMapping(asset={self.asset_id}, scene={self.script_scene_id})>"
