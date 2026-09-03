"""add script models

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create script-related tables: scripts, script_scenes, script_characters, script_dialogues."""
    # Scripts table
    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("logline", sa.String(length=500), nullable=True),
        sa.Column("genre", sa.String(length=50), nullable=True),
        sa.Column("style", sa.String(length=100), nullable=True),
        sa.Column("total_episodes", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("synopsis", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=False, server_default="v0.1"),
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
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scripts_id"), "scripts", ["id"], unique=False)
    op.create_index(op.f("ix_scripts_project_id"), "scripts", ["project_id"], unique=False)
    op.create_index(op.f("ix_scripts_title"), "scripts", ["title"], unique=False)
    op.create_index(op.f("ix_scripts_genre"), "scripts", ["genre"], unique=False)

    # Script scenes table
    op.create_table(
        "script_scenes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("scene_number", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column(
            "int_ext",
            sa.Enum("INT", "EXT", "INT/EXT", name="intext"),
            nullable=False,
            server_default="INT",
        ),
        sa.Column(
            "time_of_day",
            sa.Enum("日", "夜", "晨", "昏", "不限", name="timeofday"),
            nullable=False,
            server_default="日",
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_scenes_id"), "script_scenes", ["id"], unique=False)
    op.create_index(op.f("ix_script_scenes_script_id"), "script_scenes", ["script_id"], unique=False)
    op.create_index(
        op.f("ix_script_scenes_order_index"), "script_scenes", ["order_index"], unique=False
    )

    # Script characters table
    op.create_table(
        "script_characters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("script_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "character_type",
            sa.Enum("主角", "配角", "客串", "龙套", name="charactertype"),
            nullable=False,
            server_default="配角",
        ),
        sa.Column("age", sa.String(length=50), nullable=True),
        sa.Column("appearance", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_characters_id"), "script_characters", ["id"], unique=False)
    op.create_index(
        op.f("ix_script_characters_script_id"), "script_characters", ["script_id"], unique=False
    )
    op.create_index(op.f("ix_script_characters_name"), "script_characters", ["name"], unique=False)

    # Script dialogues table
    op.create_table(
        "script_dialogues",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scene_id", sa.Integer(), nullable=False),
        sa.Column("character_id", sa.Integer(), nullable=True),
        sa.Column("character_name", sa.String(length=100), nullable=False),
        sa.Column("dialogue", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=500), nullable=True),
        sa.Column(
            "emotion",
            sa.Enum(
                "正常",
                "开心",
                "悲伤",
                "愤怒",
                "惊讶",
                "恐惧",
                "紧张",
                "平静",
                "兴奋",
                "自信",
                "讽刺",
                "冷漠",
                "温柔",
                name="emotion",
            ),
            nullable=False,
            server_default="正常",
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["scene_id"], ["script_scenes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["character_id"], ["script_characters.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_script_dialogues_id"), "script_dialogues", ["id"], unique=False)
    op.create_index(
        op.f("ix_script_dialogues_scene_id"), "script_dialogues", ["scene_id"], unique=False
    )
    op.create_index(
        op.f("ix_script_dialogues_character_id"),
        "script_dialogues",
        ["character_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_script_dialogues_order_index"),
        "script_dialogues",
        ["order_index"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all script-related tables and enums."""
    op.drop_index(op.f("ix_script_dialogues_order_index"), table_name="script_dialogues")
    op.drop_index(op.f("ix_script_dialogues_character_id"), table_name="script_dialogues")
    op.drop_index(op.f("ix_script_dialogues_scene_id"), table_name="script_dialogues")
    op.drop_index(op.f("ix_script_dialogues_id"), table_name="script_dialogues")
    op.drop_table("script_dialogues")

    op.drop_index(op.f("ix_script_characters_name"), table_name="script_characters")
    op.drop_index(op.f("ix_script_characters_script_id"), table_name="script_characters")
    op.drop_index(op.f("ix_script_characters_id"), table_name="script_characters")
    op.drop_table("script_characters")

    op.drop_index(op.f("ix_script_scenes_order_index"), table_name="script_scenes")
    op.drop_index(op.f("ix_script_scenes_script_id"), table_name="script_scenes")
    op.drop_index(op.f("ix_script_scenes_id"), table_name="script_scenes")
    op.drop_table("script_scenes")

    op.drop_index(op.f("ix_scripts_genre"), table_name="scripts")
    op.drop_index(op.f("ix_scripts_title"), table_name="scripts")
    op.drop_index(op.f("ix_scripts_project_id"), table_name="scripts")
    op.drop_index(op.f("ix_scripts_id"), table_name="scripts")
    op.drop_table("scripts")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS emotion")
    op.execute("DROP TYPE IF EXISTS charactertype")
    op.execute("DROP TYPE IF EXISTS timeofday")
    op.execute("DROP TYPE IF EXISTS intext")