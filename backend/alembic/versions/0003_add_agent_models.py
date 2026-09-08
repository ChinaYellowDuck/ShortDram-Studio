"""add agent models and llm_config.model_type

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agents, agent_runs, agent_run_steps tables + llm_configs.model_type."""
    # Clean up any leftover enum types from previous failed runs (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS runstatus CASCADE")
    op.execute("DROP TYPE IF EXISTS stepstatus CASCADE")

    # Add model_type column to llm_configs
    op.add_column(
        "llm_configs",
        sa.Column(
            "model_type",
            sa.String(length=20),
            nullable=False,
            server_default="text",
        ),
    )
    op.create_index(op.f("ix_llm_configs_model_type"), "llm_configs", ["model_type"], unique=False)

    # Agents table
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_key", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("default_llm_config_id", sa.Integer(), nullable=True),
        sa.Column("default_params", sa.JSON(), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["default_llm_config_id"], ["llm_configs.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agents_id"), "agents", ["id"], unique=False)
    op.create_index(op.f("ix_agents_agent_key"), "agents", ["agent_key"], unique=True)
    op.create_index(op.f("ix_agents_agent_type"), "agents", ["agent_type"], unique=False)
    op.create_index(op.f("ix_agents_is_enabled"), "agents", ["is_enabled"], unique=False)
    op.create_index(
        op.f("ix_agents_default_llm_config_id"),
        "agents",
        ["default_llm_config_id"],
        unique=False,
    )

    # Agent runs table
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="runstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("llm_config_id", sa.Integer(), nullable=True),
        sa.Column("llm_model_name", sa.String(length=100), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["llm_config_id"], ["llm_configs.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_id"), "agent_runs", ["id"], unique=False)
    op.create_index(op.f("ix_agent_runs_agent_id"), "agent_runs", ["agent_id"], unique=False)
    op.create_index(
        op.f("ix_agent_runs_project_id"), "agent_runs", ["project_id"], unique=False
    )
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"], unique=False)

    # Agent run steps table
    op.create_table(
        "agent_run_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(length=100), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                "skipped",
                name="stepstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_run_steps_id"), "agent_run_steps", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_run_steps_run_id"), "agent_run_steps", ["run_id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_run_steps_step_name"), "agent_run_steps", ["step_name"], unique=False
    )
    op.create_index(
        op.f("ix_agent_run_steps_status"), "agent_run_steps", ["status"], unique=False
    )


def downgrade() -> None:
    """Drop agent tables, enums, and llm_configs.model_type."""
    op.drop_index(op.f("ix_agent_run_steps_status"), table_name="agent_run_steps")
    op.drop_index(op.f("ix_agent_run_steps_step_name"), table_name="agent_run_steps")
    op.drop_index(op.f("ix_agent_run_steps_run_id"), table_name="agent_run_steps")
    op.drop_index(op.f("ix_agent_run_steps_id"), table_name="agent_run_steps")
    op.drop_table("agent_run_steps")

    op.drop_index(op.f("ix_agent_runs_status"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_project_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_agent_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_id"), table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index(op.f("ix_agents_default_llm_config_id"), table_name="agents")
    op.drop_index(op.f("ix_agents_is_enabled"), table_name="agents")
    op.drop_index(op.f("ix_agents_agent_type"), table_name="agents")
    op.drop_index(op.f("ix_agents_agent_key"), table_name="agents")
    op.drop_index(op.f("ix_agents_id"), table_name="agents")
    op.drop_table("agents")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS stepstatus")
    op.execute("DROP TYPE IF EXISTS runstatus")

    # Drop model_type column and index
    op.drop_index(op.f("ix_llm_configs_model_type"), table_name="llm_configs")
    op.drop_column("llm_configs", "model_type")
