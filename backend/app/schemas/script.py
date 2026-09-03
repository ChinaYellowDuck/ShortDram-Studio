"""Pydantic schemas for Script, Scene, Character, and Dialogue."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.script import CharacterType, Emotion, IntExt, TimeOfDay


# ── Character ────────────────────────────────────────────────────────────────

class ScriptCharacterBase(BaseModel):
    """Base schema for a script character."""

    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述/人物小传")
    character_type: CharacterType = Field(
        default=CharacterType.SUPPORTING, description="角色类型"
    )
    age: Optional[str] = Field(None, max_length=50, description="年龄")
    appearance: Optional[str] = Field(None, description="外貌描述")


class ScriptCharacterCreate(ScriptCharacterBase):
    """Schema for creating a character."""

    pass


class ScriptCharacterUpdate(BaseModel):
    """Schema for updating a character (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    character_type: Optional[CharacterType] = None
    age: Optional[str] = None
    appearance: Optional[str] = None


class ScriptCharacterResponse(ScriptCharacterBase):
    """Schema for character response."""

    id: int
    script_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Dialogue ─────────────────────────────────────────────────────────────────

class ScriptDialogueBase(BaseModel):
    """Base schema for a dialogue line."""

    character_name: str = Field(..., min_length=1, max_length=100, description="角色名")
    dialogue: str = Field(..., min_length=1, description="台词内容")
    action: Optional[str] = Field(None, max_length=500, description="动作提示/括号提示")
    emotion: Emotion = Field(default=Emotion.NORMAL, description="情绪")
    character_id: Optional[int] = Field(None, description="关联角色ID")
    order_index: int = Field(default=0, description="排序")


class ScriptDialogueCreate(ScriptDialogueBase):
    """Schema for creating a dialogue line."""

    pass


class ScriptDialogueUpdate(BaseModel):
    """Schema for updating a dialogue line."""

    character_name: Optional[str] = Field(None, min_length=1, max_length=100)
    dialogue: Optional[str] = None
    action: Optional[str] = None
    emotion: Optional[Emotion] = None
    character_id: Optional[int] = None
    order_index: Optional[int] = None


class ScriptDialogueResponse(ScriptDialogueBase):
    """Schema for dialogue response."""

    id: int
    scene_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Scene ────────────────────────────────────────────────────────────────────

class ScriptSceneBase(BaseModel):
    """Base schema for a script scene."""

    scene_number: str = Field(..., max_length=20, description="场景号")
    location: str = Field(..., min_length=1, max_length=200, description="场景地点")
    int_ext: IntExt = Field(default=IntExt.INT, description="内景/外景")
    time_of_day: TimeOfDay = Field(default=TimeOfDay.DAY, description="时间")
    description: Optional[str] = Field(None, description="场景描述/动作描写")
    order_index: int = Field(default=0, description="排序")


class ScriptSceneCreate(ScriptSceneBase):
    """Schema for creating a scene."""

    pass


class ScriptSceneUpdate(BaseModel):
    """Schema for updating a scene."""

    scene_number: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = None
    int_ext: Optional[IntExt] = None
    time_of_day: Optional[TimeOfDay] = None
    description: Optional[str] = None
    order_index: Optional[int] = None


class ScriptSceneResponse(ScriptSceneBase):
    """Schema for scene response (with dialogues)."""

    id: int
    script_id: int
    dialogues: list[ScriptDialogueResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptSceneSimpleResponse(ScriptSceneBase):
    """Schema for scene response without dialogues (used in list views)."""

    id: int
    script_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Script ───────────────────────────────────────────────────────────────────

class ScriptBase(BaseModel):
    """Base schema for a script."""

    title: str = Field(..., min_length=1, max_length=200, description="剧本标题")
    logline: Optional[str] = Field(None, max_length=500, description="一句话梗概")
    genre: Optional[str] = Field(None, max_length=50, description="题材")
    style: Optional[str] = Field(None, max_length=100, description="风格")
    total_episodes: int = Field(default=1, ge=1, description="总集数")
    synopsis: Optional[str] = Field(None, description="故事大纲")
    version: str = Field(default="v0.1", max_length=50, description="版本")


class ScriptCreate(ScriptBase):
    """Schema for creating a script."""

    project_id: int = Field(..., description="所属项目ID")


class ScriptUpdate(BaseModel):
    """Schema for updating a script."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    logline: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    total_episodes: Optional[int] = None
    synopsis: Optional[str] = None
    version: Optional[str] = None


class ScriptResponse(ScriptBase):
    """Schema for script response with basic info (no nested scenes/characters)."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptDetailResponse(ScriptBase):
    """Schema for full script response including scenes and characters."""

    id: int
    project_id: int
    scenes: list[ScriptSceneResponse] = []
    characters: list[ScriptCharacterResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Generation Request ───────────────────────────────────────────────────────

class ScriptGenerateRequest(BaseModel):
    """Request schema for AI script generation."""

    idea: str = Field(..., min_length=5, description="创意描述")
    genre: str = Field(default="都市", max_length=50, description="题材")
    style: Optional[str] = Field(None, max_length=100, description="风格")
    num_scenes: int = Field(default=10, ge=1, le=100, description="生成场景数量")
    llm_config_id: Optional[int] = Field(None, description="使用的LLM配置ID，不填用默认")


class ScriptRefineRequest(BaseModel):
    """Request schema for refining a scene or the whole script."""

    script_id: int = Field(..., description="剧本ID")
    scene_id: Optional[int] = Field(None, description="场景ID，不填则打磨整个剧本")
    feedback: str = Field(..., min_length=2, description="修改意见/反馈")
    llm_config_id: Optional[int] = Field(None, description="使用的LLM配置ID，不填用默认")


class ScriptFountainExport(BaseModel):
    """Fountain format export response."""

    script_id: int
    title: str
    content: str
    format: str = "fountain"