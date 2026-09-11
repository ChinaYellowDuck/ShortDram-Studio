"""Project model."""
import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ProjectStatus(str, enum.Enum):
    """Project lifecycle status."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectPhase(str, enum.Enum):
    """Project production phase (linear workflow).

    Phases: setup → script → asset → storyboard → video → completed.
    """

    SETUP = "setup"
    SCRIPT = "script"
    ASSET = "asset"
    STORYBOARD = "storyboard"
    VIDEO = "video"
    COMPLETED = "completed"


class Project(BaseModel):
    """Short drama project model.

    A project is the top-level container for all short drama production assets,
    including scripts, characters, storyboards, voiceovers, and final videos.

    Attributes:
        name: Project name.
        description: Project description.
        status: Current project status.
        cover_image: Optional cover image URL/path.
    """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProjectStatus.DRAFT,
        index=True,
    )
    phase: Mapped[ProjectPhase] = mapped_column(
        Enum(ProjectPhase, values_callable=lambda x: [e.value for e in x]),
        default=ProjectPhase.SETUP,
        index=True,
    )
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
