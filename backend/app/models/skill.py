"""Skill model."""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Skill(BaseModel):
    """A reusable skill that can be bound to agents.

    Attributes:
        name: Unique display name.
        description: Optional description.
        content: Instructions/prompt content for the skill.
        is_enabled: Whether the skill is active.
    """

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}')>"
