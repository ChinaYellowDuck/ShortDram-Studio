"""Script related models.

Includes Script (main), ScriptScene, ScriptCharacter, and ScriptDialogue.
A script belongs to a project and contains multiple scenes, characters, and dialogues.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class IntExt(str, enum.Enum):
    """Interior / Exterior location type."""

    INT = "INT"  # 内景
    EXT = "EXT"  # 外景
    INT_EXT = "INT/EXT"  # 内外景结合


class TimeOfDay(str, enum.Enum):
    """Time of day for a scene."""

    DAY = "日"
    NIGHT = "夜"
    DAWN = "晨"
    DUSK = "昏"
    ANY = "不限"


class CharacterType(str, enum.Enum):
    """Character role type."""

    LEAD = "主角"
    SUPPORTING = "配角"
    CAMEO = "客串"
    EXTRA = "龙套"


class Emotion(str, enum.Enum):
    """Common emotions for dialogue delivery."""

    NORMAL = "正常"
    HAPPY = "开心"
    SAD = "悲伤"
    ANGRY = "愤怒"
    SURPRISED = "惊讶"
    FEARFUL = "恐惧"
    NERVOUS = "紧张"
    CALM = "平静"
    EXCITED = "兴奋"
    CONFIDENT = "自信"
    SARCASTIC = "讽刺"
    COLD = "冷漠"
    TENDER = "温柔"


class Script(BaseModel):
    """Short drama script model.

    A script is the core creative document of a project, containing
    scenes, characters, and dialogues.

    Attributes:
        project_id: Associated project ID.
        title: Script title.
        logline: One-sentence story premise.
        genre: Genre category (urban, xianxia, romance, thriller, etc.).
        style: Writing style / tone.
        total_episodes: Number of episodes planned.
        synopsis: Full story synopsis.
        version: Version number / tag.
    """

    __tablename__ = "scripts"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    logline: Mapped[str | None] = mapped_column(String(500), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_episodes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), default="v0.1", nullable=False)

    # Relationships
    scenes: Mapped[list["ScriptScene"]] = relationship(
        "ScriptScene",
        back_populates="script",
        cascade="all, delete-orphan",
        order_by="ScriptScene.order_index",
    )
    characters: Mapped[list["ScriptCharacter"]] = relationship(
        "ScriptCharacter",
        back_populates="script",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Script(id={self.id}, title='{self.title}', project_id={self.project_id})>"


class ScriptScene(BaseModel):
    """A single scene in a script.

    Attributes:
        script_id: Parent script ID.
        scene_number: Human-readable scene number (e.g. "1", "2A").
        location: Location name / setting.
        int_ext: Interior / Exterior type.
        time_of_day: Time of day.
        description: Scene description / action lines.
        order_index: Sort order within the script.
    """

    __tablename__ = "script_scenes"

    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scene_number: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    int_ext: Mapped[IntExt] = mapped_column(
        Enum(IntExt, values_callable=lambda x: [e.value for e in x]),
        default=IntExt.INT,
        nullable=False,
    )
    time_of_day: Mapped[TimeOfDay] = mapped_column(
        Enum(TimeOfDay, values_callable=lambda x: [e.value for e in x]),
        default=TimeOfDay.DAY,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # Relationships
    script: Mapped[Script] = relationship("Script", back_populates="scenes")
    dialogues: Mapped[list["ScriptDialogue"]] = relationship(
        "ScriptDialogue",
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="ScriptDialogue.order_index",
    )

    def __repr__(self) -> str:
        return (
            f"<ScriptScene(id={self.id}, scene_number='{self.scene_number}', "
            f"location='{self.location}')>"
        )


class ScriptCharacter(BaseModel):
    """A character in a script.

    Attributes:
        script_id: Parent script ID.
        name: Character name.
        description: Character description / bio.
        character_type: Lead / Supporting / Cameo / Extra.
        age: Approximate age.
        appearance: Physical appearance description.
    """

    __tablename__ = "script_characters"

    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    character_type: Mapped[CharacterType] = mapped_column(
        Enum(CharacterType, values_callable=lambda x: [e.value for e in x]),
        default=CharacterType.SUPPORTING,
        nullable=False,
    )
    age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    appearance: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    script: Mapped[Script] = relationship("Script", back_populates="characters")

    def __repr__(self) -> str:
        return f"<ScriptCharacter(id={self.id}, name='{self.name}')>"


class ScriptDialogue(BaseModel):
    """A single dialogue line in a scene.

    Attributes:
        scene_id: Parent scene ID.
        character_id: Speaking character ID (nullable for narration / off-screen).
        character_name: Character name display (denormalized for quick rendering).
        dialogue: The spoken line text.
        action: Parenthetical / action description before the line.
        emotion: Emotion tag for voice direction.
        order_index: Sort order within the scene.
    """

    __tablename__ = "script_dialogues"

    scene_id: Mapped[int] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[int | None] = mapped_column(
        ForeignKey("script_characters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    character_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dialogue: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emotion: Mapped[Emotion] = mapped_column(
        Enum(Emotion, values_callable=lambda x: [e.value for e in x]),
        default=Emotion.NORMAL,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # Relationships
    scene: Mapped["ScriptScene"] = relationship("ScriptScene", back_populates="dialogues")

    def __repr__(self) -> str:
        return (
            f"<ScriptDialogue(id={self.id}, character='{self.character_name}', "
            f"scene_id={self.scene_id})>"
        )