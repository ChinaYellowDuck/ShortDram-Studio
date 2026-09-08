"""add agent run step composite index

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add a composite (run_id, step_index) index for step ordering."""
    op.create_index(
        "ix_agent_run_steps_run_id_step_index",
        "agent_run_steps",
        ["run_id", "step_index"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the composite index."""
    op.drop_index("ix_agent_run_steps_run_id_step_index", table_name="agent_run_steps")
