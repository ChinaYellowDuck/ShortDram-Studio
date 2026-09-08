"""add mcp and skill models, and agent associations

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add mcps, skills, association tables, and agent columns."""
    op.create_table(
        "mcps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("transport", sa.String(length=50), nullable=False, server_default="streamable_http"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mcps_id"), "mcps", ["id"], unique=False)
    op.create_index(op.f("ix_mcps_name"), "mcps", ["name"], unique=True)
    op.create_index(op.f("ix_mcps_is_enabled"), "mcps", ["is_enabled"], unique=False)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skills_id"), "skills", ["id"], unique=False)
    op.create_index(op.f("ix_skills_name"), "skills", ["name"], unique=True)
    op.create_index(op.f("ix_skills_is_enabled"), "skills", ["is_enabled"], unique=False)

    op.create_table(
        "agent_mcp",
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("mcp_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mcp_id"], ["mcps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_id", "mcp_id"),
    )

    op.create_table(
        "agent_skill",
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_id", "skill_id"),
    )

    op.add_column("agents", sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"))
    op.add_column("agents", sa.Column("system_message", sa.Text(), nullable=True))


def downgrade() -> None:
    """Drop MCP/skill tables, associations, and agent columns."""
    op.drop_column("agents", "system_message")
    op.drop_column("agents", "temperature")

    op.drop_table("agent_skill")
    op.drop_table("agent_mcp")

    op.drop_index(op.f("ix_skills_is_enabled"), table_name="skills")
    op.drop_index(op.f("ix_skills_name"), table_name="skills")
    op.drop_index(op.f("ix_skills_id"), table_name="skills")
    op.drop_table("skills")

    op.drop_index(op.f("ix_mcps_is_enabled"), table_name="mcps")
    op.drop_index(op.f("ix_mcps_name"), table_name="mcps")
    op.drop_index(op.f("ix_mcps_id"), table_name="mcps")
    op.drop_table("mcps")
