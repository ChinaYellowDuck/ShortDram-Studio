"""add_mcp_fields

Add mcp_type, secrets, and tools columns to mcps table.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-11
"""
from alembic import op
import sqlalchemy as sa


revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mcps", sa.Column("mcp_type", sa.String(length=30), nullable=True))
    op.add_column("mcps", sa.Column("secrets", sa.JSON(), nullable=True))
    op.add_column("mcps", sa.Column("tools", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_mcps_mcp_type"), "mcps", ["mcp_type"], unique=False)

    # Set default for existing rows
    op.execute("UPDATE mcps SET mcp_type = 'custom' WHERE mcp_type IS NULL")

    # Make it NOT NULL with default
    op.alter_column("mcps", "mcp_type", existing_type=sa.String(length=30), nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mcps_mcp_type"), table_name="mcps")
    op.drop_column("mcps", "tools")
    op.drop_column("mcps", "secrets")
    op.drop_column("mcps", "mcp_type")
