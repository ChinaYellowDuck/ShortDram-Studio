"""Agent models: agent metadata, agent runs, and agent run steps."""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


# Many-to-many association tables
agent_mcp = Table(
    "agent_mcp",
    BaseModel.metadata,
    Column("agent_id", Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("mcp_id", Integer, ForeignKey("mcps.id", ondelete="CASCADE"), primary_key=True),
)

agent_skill = Table(
    "agent_skill",
    BaseModel.metadata,
    Column("agent_id", Integer, ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class RunStatus(str, PyEnum):
    """Status of an agent run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, PyEnum):
    """Status of an agent run step (graph node execution)."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Agent(BaseModel):
    """Agent metadata model.

    Stores the registry of available agents so they can be managed
    (enabled/disabled, configured with default LLM, etc.) through the UI.

    Attributes:
        agent_key: Business-unique key (e.g. "screenwriter", "producer") used
            to map to the concrete Agent class in code.
        name: Human-readable display name.
        description: Short description of what the agent does.
        agent_type: Agent category (创作/协调/角色设计/分镜/配音/剪辑/测试 etc.).
        category: Display category tag.
        is_enabled: Whether this agent is available for use.
        default_llm_config_id: Default LLM configuration to use.
        default_params: Default custom parameters as a JSON dict.
        version: Agent version string.
    """

    __tablename__ = "agents"

    agent_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    default_llm_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    default_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    system_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)

    # Relationships
    default_llm_config = relationship("LLMConfig", foreign_keys=[default_llm_config_id])
    runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="agent", passive_deletes=True
    )
    mcps: Mapped[list["Mcp"]] = relationship(
        "Mcp", secondary=agent_mcp, lazy="selectin"
    )
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", secondary=agent_skill, lazy="selectin"
    )

    @property
    def mcp_ids(self) -> list[int]:
        """Bound MCP server IDs."""
        return [m.id for m in self.mcps]

    @property
    def skill_ids(self) -> list[int]:
        """Bound skill IDs."""
        return [s.id for s in self.skills]

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, key='{self.agent_key}', name='{self.name}')>"


class AgentRun(BaseModel):
    """Record of a single agent execution.

    Attributes:
        agent_id: Reference to the agent metadata (null if agent was deleted).
        project_id: Reference to the project this run belongs to (optional).
        status: Current run status.
        llm_config_id: LLM config used for this run.
        llm_model_name: Snapshot of the model name used.
        input_summary: Truncated input summary.
        output_summary: Truncated output summary.
        error_message: Error details if status is failed.
        duration_ms: Total duration in milliseconds.
        total_tokens: Total token consumption (if available).
        started_at: When execution actually started.
        finished_at: When execution finished (success or failure).
    """

    __tablename__ = "agent_runs"

    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, values_callable=lambda enum: [item.value for item in enum], name="runstatus"),
        default=RunStatus.PENDING,
        nullable=False,
        index=True,
    )
    llm_config_id: Mapped[int | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"), nullable=True
    )
    llm_model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    agent: Mapped["Agent | None"] = relationship("Agent", back_populates="runs")
    project = relationship("Project")
    llm_config = relationship("LLMConfig")
    steps: Mapped[list["AgentRunStep"]] = relationship(
        "AgentRunStep",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="AgentRunStep.step_index",
    )

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent_id={self.agent_id}, status={self.status.value})>"


class AgentRunStep(BaseModel):
    """Record of a single graph node execution within an agent run.

    Attributes:
        run_id: Parent agent run.
        step_name: LangGraph node name.
        step_index: Sequential index within the run (increments for looped nodes).
        status: Step execution status.
        input_summary: Truncated input to the node.
        output_summary: Truncated output of the node.
        error_message: Error details if status is failed.
        duration_ms: Step duration in milliseconds.
        tokens_used: Token consumption for this step (if available).
        started_at: When the step started.
        finished_at: When the step finished.
    """

    __tablename__ = "agent_run_steps"
    __table_args__ = (Index("ix_agent_run_steps_run_id_step_index", "run_id", "step_index"),)

    run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus, values_callable=lambda enum: [item.value for item in enum], name="stepstatus"),
        default=StepStatus.PENDING,
        nullable=False,
        index=True,
    )
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="steps")

    def __repr__(self) -> str:
        return (
            f"<AgentRunStep(id={self.id}, run_id={self.run_id}, "
            f"step='{self.step_name}' idx={self.step_index})>"
        )
