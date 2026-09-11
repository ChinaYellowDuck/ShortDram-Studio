"""add generation_stage and script_episodes

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-11 15:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first
    script_generation_stage = sa.Enum(
        "idea", "outline", "characters", "episodes", "completed",
        name="scriptgenerationstage",
    )
    script_generation_stage.create(op.get_bind())

    # Add new columns to scripts
    op.add_column(
        "scripts",
        sa.Column(
            "generation_stage",
            script_generation_stage,
            nullable=False,
            server_default="idea",
        ),
    )
    op.add_column("scripts", sa.Column("episode_outlines", sa.JSON(), nullable=True))
    op.add_column("scripts", sa.Column("core_idea", sa.Text(), nullable=True))
    op.create_index(op.f("ix_scripts_generation_stage"), "scripts", ["generation_stage"], unique=False)

    # Create script_episodes table
    op.create_table(
        "script_episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("is_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_episodes_script_id"), "script_episodes", ["script_id"], unique=False)
    op.create_index(op.f("ix_script_episodes_order_index"), "script_episodes", ["order_index"], unique=False)
    op.create_foreign_key(
        "fk_script_episodes_script_id",
        "script_episodes",
        "scripts",
        ["script_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_table("script_episodes")
    op.drop_index(op.f("ix_scripts_generation_stage"), table_name="scripts")
    op.drop_column("scripts", "core_idea")
    op.drop_column("scripts", "episode_outlines")
    op.drop_column("scripts", "generation_stage")
    sa.Enum(name="scriptgenerationstage").drop(op.get_bind())
