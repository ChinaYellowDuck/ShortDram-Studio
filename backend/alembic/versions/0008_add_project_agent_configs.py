"""add project_agent_configs and agent seeding

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-11 16:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_agent_configs table
    op.create_table(
        "project_agent_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_director", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("llm_config_id", sa.Integer(), nullable=True),
        sa.Column("params_override", sa.JSON(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("system_message_override", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("role_description", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "agent_id", name="uq_project_agent"),
    )
    op.create_index(op.f("ix_project_agent_configs_project_id"), "project_agent_configs", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_agent_configs_agent_id"), "project_agent_configs", ["agent_id"], unique=False)
    op.create_index(op.f("ix_project_agent_configs_is_enabled"), "project_agent_configs", ["is_enabled"], unique=False)
    op.create_foreign_key(
        "fk_project_agent_configs_project_id",
        "project_agent_configs",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_project_agent_configs_agent_id",
        "project_agent_configs",
        "agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_project_agent_configs_llm_config_id",
        "project_agent_configs",
        "llm_configs",
        ["llm_config_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Seed additional agents (director, storyboard, voice, etc.)
    agents_data = [
        ('director', '总控导演', '贯穿全流程的总控智能体，负责项目整体把控、子智能体调度、质量审核与决策仲裁', '协调', '核心', 0.7),
        ('storyboard', '分镜师', '根据剧本生成专业分镜脚本，包含景别、运镜、角度、时长等设计', '创作', '视觉', 0.7),
        ('character_designer', '角色设计师', '设计剧中角色的外貌、性格、服装、造型等视觉形象', '设计', '视觉', 0.8),
        ('copywriter', '文案师', '撰写旁白、字幕、宣发文案、剧名、Tagline 等文字内容', '创作', '文字', 0.7),
        ('voice_director', '配音导演', '配音风格设计、声优选角、台词指导与配音质量把控', '音频', '声音', 0.7),
        ('video_editor', '剪辑师', '视频片段剪辑、转场设计、节奏把控与最终成片合成', '制作', '视频', 0.7),
        ('asset_collector', '素材管理员', '素材导入、分类整理、资产库管理与质量审核', '管理', '资产', 0.6),
    ]
    for key, name, desc, atype, category, temp in agents_data:
        op.execute(
            sa.text(
                "INSERT INTO agents (agent_key, name, description, agent_type, category, is_enabled, temperature, version, created_at, updated_at) "
                "VALUES (:k, :n, :d, :t, :c, true, :temp, '1.0', NOW(), NOW()) "
                "ON CONFLICT (agent_key) DO NOTHING"
            ).bindparams(k=key, n=name, d=desc, t=atype, c=category, temp=temp)
        )


def downgrade() -> None:
    op.drop_table("project_agent_configs")
    # Note: We don't delete seeded agents on downgrade to preserve data
