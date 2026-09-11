"""Project agent configuration models.

Links projects to agents with per-project overrides for
LLM config, parameters, and enabled/disabled status.
"""
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ProjectAgentConfig(BaseModel):
    """Per-project agent configuration.

    Stores whether an agent is enabled for a specific project,
    which LLM config to use, and any parameter overrides.

    Attributes:
        project_id: The project this config belongs to.
        agent_id: The agent this config is for.
        is_enabled: Whether this agent is active for this project.
        is_director: Whether this is the director/lead agent for the project.
        llm_config_id: Override LLM config (null = use agent default).
        params_override: JSON dict of parameter overrides (merged on top of agent defaults).
        temperature: Override temperature (null = use agent default).
        system_message_override: Override system prompt (null = use agent default).
        priority: Execution priority / ordering (lower = runs earlier).
    """

    __tablename__ = "project_agent_configs"
    __table_args__ = (
        UniqueConstraint("project_id", "agent_id", name="uq_project_agent"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_director: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"), nullable=True
    )
    params_override: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_message_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    role_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    agent = relationship("Agent", lazy="selectin")
    llm_config = relationship("LLMConfig")

    @property
    def agent_key(self) -> str | None:
        return self.agent.agent_key if self.agent else None

    def __repr__(self) -> str:
        return (
            f"<ProjectAgentConfig(project={self.project_id}, "
            f"agent={self.agent_id}, enabled={self.is_enabled}, "
            f"director={self.is_director})>"
        )
