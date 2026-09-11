"""add phase, asset and storyboard models

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-10 00:00:00.000000
"""
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create projectphase enum type first (needed for add_column)
    op.execute("CREATE TYPE projectphase AS ENUM ('script', 'asset', 'storyboard', 'video', 'completed')")

    # 1. phase column on projects
    op.add_column(
        "projects",
        sa.Column(
            "phase",
            sa.Enum("script", "asset", "storyboard", "video", "completed", name="projectphase"),
            nullable=False,
            server_default="script",
        ),
    )
    op.create_index(op.f("ix_projects_phase"), "projects", ["phase"], unique=False)

    # 2. assets table
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Enum("character", "scene", "prop", name="assettype"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column(
            "source",
            sa.Enum("ai_extracted", "manual", name="assetsource"),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("reference_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_project_id"), "assets", ["project_id"], unique=False)
    op.create_index(op.f("ix_assets_type"), "assets", ["type"], unique=False)
    op.create_index(op.f("ix_assets_name"), "assets", ["name"], unique=False)

    # 3. asset_script_mappings table
    op.create_table(
        "asset_script_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("script_scene_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_scene_id"], ["script_scenes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_asset_script_mappings_asset_id"), "asset_script_mappings", ["asset_id"], unique=False)
    op.create_index(op.f("ix_asset_script_mappings_script_id"), "asset_script_mappings", ["script_id"], unique=False)
    op.create_index(op.f("ix_asset_script_mappings_script_scene_id"), "asset_script_mappings", ["script_scene_id"], unique=False)

    # 4. storyboard_shots table
    op.create_table(
        "storyboard_shots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("script_scene_id", sa.Integer(), nullable=False),
        sa.Column("shot_number", sa.String(length=50), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "composition",
            sa.Enum("大远景", "远景", "全景", "中景", "中近景", "近景", "特写", name="compositiontype"),
            nullable=False,
            server_default="中景",
        ),
        sa.Column(
            "camera_movement",
            sa.Enum("固定", "推", "拉", "摇", "移", "跟", "变焦", name="cameramovement"),
            nullable=False,
            server_default="固定",
        ),
        sa.Column(
            "camera_angle",
            sa.Enum("平视", "仰视", "俯视", "侧视", "倾斜", name="cameraangle"),
            nullable=False,
            server_default="平视",
        ),
        sa.Column("visual_description", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("key_frame_url", sa.String(length=500), nullable=True),
        sa.Column("character_ids", sa.JSON(), nullable=True),
        sa.Column("prop_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_scene_id"], ["script_scenes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_storyboard_shots_project_id"), "storyboard_shots", ["project_id"], unique=False)
    op.create_index(op.f("ix_storyboard_shots_script_scene_id"), "storyboard_shots", ["script_scene_id"], unique=False)
    op.create_index(op.f("ix_storyboard_shots_order_index"), "storyboard_shots", ["order_index"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_storyboard_shots_order_index"), table_name="storyboard_shots")
    op.drop_index(op.f("ix_storyboard_shots_script_scene_id"), table_name="storyboard_shots")
    op.drop_index(op.f("ix_storyboard_shots_project_id"), table_name="storyboard_shots")
    op.drop_table("storyboard_shots")

    op.drop_index(op.f("ix_asset_script_mappings_script_scene_id"), table_name="asset_script_mappings")
    op.drop_index(op.f("ix_asset_script_mappings_script_id"), table_name="asset_script_mappings")
    op.drop_index(op.f("ix_asset_script_mappings_asset_id"), table_name="asset_script_mappings")
    op.drop_table("asset_script_mappings")

    op.drop_index(op.f("ix_assets_name"), table_name="assets")
    op.drop_index(op.f("ix_assets_type"), table_name="assets")
    op.drop_index(op.f("ix_assets_project_id"), table_name="assets")
    op.drop_table("assets")

    op.drop_index(op.f("ix_projects_phase"), table_name="projects")
    op.drop_column("projects", "phase")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS projectphase")
    op.execute("DROP TYPE IF EXISTS assettype")
    op.execute("DROP TYPE IF EXISTS assetsource")
    op.execute("DROP TYPE IF EXISTS compositiontype")
    op.execute("DROP TYPE IF EXISTS cameramovement")
    op.execute("DROP TYPE IF EXISTS cameraangle")
