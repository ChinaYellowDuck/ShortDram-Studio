"""add_setup_phase

Add 'setup' phase to project_phase enum and set it as the default for new projects.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: add new value to existing enum type
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Must be in its own transaction (autocommit) for PG
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE projectphase ADD VALUE IF NOT EXISTS 'setup'")

    # Update default for new projects
    op.alter_column(
        "projects",
        "phase",
        existing_type=sa.Enum("setup", "script", "asset", "storyboard", "video", "completed", name="projectphase"),
        server_default=None,
    )

    # Set existing draft projects to setup
    op.execute(
        "UPDATE projects SET phase = 'setup' WHERE phase = 'script' AND status = 'draft'"
    )


def downgrade() -> None:
    # Move setup-phase projects back to script
    op.execute("UPDATE projects SET phase = 'script' WHERE phase = 'setup'")

    # Note: PostgreSQL doesn't support removing enum values easily.
    # We leave the enum value in place but it won't be used.
    op.alter_column(
        "projects",
        "phase",
        existing_type=sa.Enum("setup", "script", "asset", "storyboard", "video", "completed", name="projectphase"),
        server_default=None,
    )
