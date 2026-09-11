# 项目管理四大模块 - Phase 1: 核心骨架 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建四大模块的核心数据骨架：项目阶段流转 + 资产管理 + 分镜管理，完成数据模型 + CRUD API + 基础测试。

**Architecture:** 沿用工现有的 FastAPI + SQLAlchemy + Service 层三层架构。新增 Asset、StoryboardShot 数据模型及对应的 Service、Schema、API Router。扩展 Project 模型增加 phase 字段支持五阶段流转。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PostgreSQL (dev SQLite), pytest

---

## 文件结构总览

**新增文件：**
- `app/models/asset.py` — 资产模型（Asset + AssetScriptMapping）
- `app/models/storyboard.py` — 分镜模型（StoryboardShot）
- `app/schemas/asset.py` — 资产 Pydantic Schema
- `app/schemas/storyboard.py` — 分镜 Pydantic Schema
- `app/services/asset_service.py` — 资产管理 Service
- `app/services/storyboard_service.py` — 分镜管理 Service
- `app/api/v1/assets.py` — 资产 API Router
- `app/api/v1/storyboard.py` — 分镜 API Router
- `tests/test_assets.py` — 资产 API 测试
- `tests/test_storyboard.py` — 分镜 API 测试
- `tests/test_project_phase.py` — 项目阶段流转测试
- `alembic/versions/0006_add_phase_and_asset_storyboard_models.py` — 数据库迁移

**修改文件：**
- `app/models/project.py` — 新增 ProjectPhase 枚举和 phase 字段
- `app/schemas/project.py` — 新增 phase 字段 + 阶段流转 schema
- `app/services/project_service.py` — 新增阶段流转方法
- `app/api/v1/projects.py` — 新增阶段流转 API
- `app/api/deps.py` — 新增 AssetServiceDep, StoryboardServiceDep
- `app/api/v1/router.py` — 注册 assets 和 storyboard router

---

## Task 1: Project 模型扩展 phase 字段

**Files:**
- Modify: `app/models/project.py`

- [ ] **Step 1: 添加 ProjectPhase 枚举和 phase 字段**

在 `app/models/project.py` 中，在 `ProjectStatus` 枚举之后添加：

```python
class ProjectPhase(str, enum.Enum):
    """Project production phase (linear workflow)."""

    SCRIPT = "script"
    ASSET = "asset"
    STORYBOARD = "storyboard"
    VIDEO = "video"
    COMPLETED = "completed"
```

在 `Project` 类中，`status` 字段之后添加：

```python
    phase: Mapped[ProjectPhase] = mapped_column(
        Enum(ProjectPhase, values_callable=lambda x: [e.value for e in x]),
        default=ProjectPhase.SCRIPT,
        index=True,
    )
```

- [ ] **Step 2: 验证模型 import 正常**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "from app.models.project import Project, ProjectPhase; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add app/models/project.py
git commit -m "feat: 添加 ProjectPhase 枚举和 phase 字段"
```

---

## Task 2: Project Schema 扩展 + Service 阶段流转

**Files:**
- Modify: `app/schemas/project.py`
- Modify: `app/services/project_service.py`
- Modify: `app/api/v1/projects.py`

- [ ] **Step 1: 修改 Project Schema**

在 `app/schemas/project.py` 中：

1. 修改导入：`from app.models.project import ProjectStatus, ProjectPhase`
2. 在 `ProjectCreate` 中添加：`phase: ProjectPhase = Field(default=ProjectPhase.SCRIPT, description="当前生产阶段")`
3. 在 `ProjectUpdate` 中添加：`phase: Optional[ProjectPhase] = Field(None, description="生产阶段")`
4. 在 `ProjectResponse` 中添加：`phase: ProjectPhase`
5. 文件末尾添加：

```python
class PhaseTransition(BaseModel):
    """Phase transition request."""
    target_phase: ProjectPhase = Field(..., description="目标阶段")
```

- [ ] **Step 2: 在 ProjectService 中添加 advance_phase 方法**

在 `app/services/project_service.py` 中，修改导入添加 `ProjectPhase`，然后在文件末尾添加：

```python
    def advance_phase(self, project_id: int, target_phase: ProjectPhase) -> Project:
        """Transition project to target phase.

        Both forward and backward transitions are allowed.
        Auto-updates project status when entering completed phase.
        """
        project = self.get_by_id_or_404(project_id)
        valid_phases = [
            ProjectPhase.SCRIPT,
            ProjectPhase.ASSET,
            ProjectPhase.STORYBOARD,
            ProjectPhase.VIDEO,
            ProjectPhase.COMPLETED,
        ]
        if target_phase not in valid_phases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phase: {target_phase}",
            )

        project.phase = target_phase
        if target_phase == ProjectPhase.COMPLETED:
            project.status = ProjectStatus.COMPLETED
        elif project.status == ProjectStatus.DRAFT and target_phase != ProjectPhase.SCRIPT:
            project.status = ProjectStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(project)
        return project
```

- [ ] **Step 3: 添加阶段流转 API 端点**

在 `app/api/v1/projects.py` 的导入中添加：
```python
from app.models.project import ProjectPhase
from app.schemas.project import PhaseTransition
```

在 delete_project 之后添加：

```python
@router.post("/{project_id}/phase", response_model=ProjectResponse, summary="切换项目阶段")
def transition_phase(
    project_id: int,
    transition: PhaseTransition,
    service: ProjectServiceDep,
):
    """Transition project to a target production phase."""
    return service.advance_phase(project_id, transition.target_phase)
```

- [ ] **Step 4: 验证 import 正常**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "
from app.schemas.project import PhaseTransition
from app.services.project_service import ProjectService
print('OK')
"
```
Expected: `OK`

- [ ] **Step 5: 提交**

```bash
git add app/schemas/project.py app/services/project_service.py app/api/v1/projects.py
git commit -m "feat: 实现项目阶段流转 API"
```

---

## Task 3: 资产数据模型

**Files:**
- Create: `app/models/asset.py`

- [ ] **Step 1: 创建资产模型文件**

创建 `app/models/asset.py`：

```python
"""Asset related models.

Three asset types: character, scene, prop.
All assets belong to a project and can be referenced by storyboard shots.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AssetType(str, enum.Enum):
    """Type of asset."""

    CHARACTER = "character"
    SCENE = "scene"
    PROP = "prop"


class AssetSource(str, enum.Enum):
    """Source of the asset."""

    AI_EXTRACTED = "ai_extracted"
    MANUAL = "manual"


class Asset(BaseModel):
    """Production asset for a project.

    Attributes:
        project_id: Owning project ID.
        type: character / scene / prop.
        name: Asset display name.
        description: Detailed description for AI generation.
        image_url: Reference image URL/path.
        metadata: Type-specific fields as JSON.
        source: How the asset was created.
        reference_count: Number of references across the project.
    """

    __tablename__ = "assets"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    source: Mapped[AssetSource] = mapped_column(
        Enum(AssetSource, values_callable=lambda x: [e.value for e in x]),
        default=AssetSource.MANUAL,
        nullable=False,
    )
    reference_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.type}')>"


class AssetScriptMapping(BaseModel):
    """Mapping between assets and script scenes.

    Tracks where each asset appears in the script.
    """

    __tablename__ = "asset_script_mappings"

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_id: Mapped[int] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_scene_id: Mapped[int | None] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    role: Mapped[str | None] = mapped_column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<AssetScriptMapping(asset={self.asset_id}, scene={self.script_scene_id})>"
```

- [ ] **Step 2: 验证 import**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "from app.models.asset import Asset, AssetType, AssetSource; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add app/models/asset.py
git commit -m "feat: 添加资产数据模型"
```

---

## Task 4: 分镜数据模型

**Files:**
- Create: `app/models/storyboard.py`

- [ ] **Step 1: 创建分镜模型文件**

创建 `app/models/storyboard.py`：

```python
"""Storyboard related models.

Scene-level granularity: one ScriptScene = one StoryboardShot.
"""
import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CompositionType(str, enum.Enum):
    """Shot composition / framing."""

    EXTREME_LONG = "大远景"
    LONG = "远景"
    FULL = "全景"
    MEDIUM = "中景"
    MEDIUM_CLOSE = "中近景"
    CLOSE_UP = "近景"
    EXTREME_CLOSE = "特写"


class CameraMovement(str, enum.Enum):
    """Camera movement type."""

    FIXED = "固定"
    PUSH_IN = "推"
    PULL_OUT = "拉"
    PAN = "摇"
    TRACK = "移"
    FOLLOW = "跟"
    ZOOM = "变焦"


class CameraAngle(str, enum.Enum):
    """Camera angle."""

    EYE_LEVEL = "平视"
    LOW_ANGLE = "仰视"
    HIGH_ANGLE = "俯视"
    SIDE = "侧视"
    DUTCH = "倾斜"


class StoryboardShot(BaseModel):
    """A single storyboard shot (scene-level granularity).

    Attributes:
        project_id: Owning project ID.
        script_scene_id: Associated script scene.
        shot_number: Human-readable shot number.
        order_index: Sort order within the project.
        composition: Shot framing type.
        camera_movement: Camera movement type.
        camera_angle: Camera angle.
        visual_description: Detailed visual prompt for video generation.
        duration_seconds: Estimated duration.
        key_frame_url: Key frame preview image.
        character_ids: JSON array of character asset IDs in this shot.
        prop_ids: JSON array of prop asset IDs in this shot.
    """

    __tablename__ = "storyboard_shots"

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_scene_id: Mapped[int] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shot_number: Mapped[str] = mapped_column(String(50), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    composition: Mapped[CompositionType] = mapped_column(
        Enum(CompositionType, values_callable=lambda x: [e.value for e in x]),
        default=CompositionType.MEDIUM,
        nullable=False,
    )
    camera_movement: Mapped[CameraMovement] = mapped_column(
        Enum(CameraMovement, values_callable=lambda x: [e.value for e in x]),
        default=CameraMovement.FIXED,
        nullable=False,
    )
    camera_angle: Mapped[CameraAngle] = mapped_column(
        Enum(CameraAngle, values_callable=lambda x: [e.value for e in x]),
        default=CameraAngle.EYE_LEVEL,
        nullable=False,
    )
    visual_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    key_frame_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    character_ids: Mapped[list | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )
    prop_ids: Mapped[list | None] = mapped_column(
        JSONB().with_variant(Text, "sqlite"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<StoryboardShot(id={self.id}, shot_number='{self.shot_number}')>"
```

- [ ] **Step 2: 验证 import**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "from app.models.storyboard import StoryboardShot, CompositionType; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add app/models/storyboard.py
git commit -m "feat: 添加分镜数据模型"
```

---

## Task 5: Alembic 数据库迁移

**Files:**
- Create: `alembic/versions/0006_add_phase_and_asset_storyboard_models.py`

- [ ] **Step 1: 创建迁移文件**

创建 `alembic/versions/0006_add_phase_and_asset_storyboard_models.py`：

```python
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
        sa.Column("metadata", sa.Text(), nullable=True),
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
        sa.Column("character_ids", sa.Text(), nullable=True),
        sa.Column("prop_ids", sa.Text(), nullable=True),
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

    op.execute("DROP TYPE IF EXISTS projectphase")
    op.execute("DROP TYPE IF EXISTS assettype")
    op.execute("DROP TYPE IF EXISTS assetsource")
    op.execute("DROP TYPE IF EXISTS compositiontype")
    op.execute("DROP TYPE IF EXISTS cameramovement")
    op.execute("DROP TYPE IF EXISTS cameraangle")
```

- [ ] **Step 2: 运行迁移**

```bash
cd D:/code/ShortDram-Studio/backend && alembic upgrade head
```
Expected: 迁移成功输出

- [ ] **Step 3: 验证表创建成功**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "
from app.database import Base, engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', [t for t in tables if 'asset' in t or 'storyboard' in t or 'project' in t])
"
```
Expected: 包含 assets, asset_script_mappings, storyboard_shots, projects

- [ ] **Step 4: 提交**

```bash
git add alembic/versions/0006_add_phase_and_asset_storyboard_models.py
git commit -m "feat: 添加 phase/资产/分镜数据库迁移 (0006)"
```

---

## Task 6: 资产 Schema + Service

**Files:**
- Create: `app/schemas/asset.py`
- Create: `app/services/asset_service.py`

- [ ] **Step 1: 创建资产 Schema**

创建 `app/schemas/asset.py`：

```python
"""Pydantic schemas for Asset."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.asset import AssetType, AssetSource


class AssetBase(BaseModel):
    type: AssetType = Field(..., description="资产类型: character/scene/prop")
    name: str = Field(..., min_length=1, max_length=200, description="资产名称")
    description: Optional[str] = Field(None, description="详细描述")
    image_url: Optional[str] = Field(None, max_length=500, description="图片 URL")
    metadata: Optional[dict] = Field(None, description="类型扩展字段")


class AssetCreate(AssetBase):
    source: AssetSource = Field(default=AssetSource.MANUAL, description="来源")


class AssetUpdate(BaseModel):
    type: Optional[AssetType] = Field(None)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = Field(None)
    source: Optional[AssetSource] = Field(None)


class AssetResponse(AssetBase):
    id: int
    source: AssetSource
    reference_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: 创建资产 Service**

创建 `app/services/asset_service.py`：

```python
"""Asset service - business logic for asset management."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetScriptMapping, AssetType
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    """Service for managing project assets."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, asset_id: int) -> Optional[Asset]:
        return self.db.query(Asset).filter(Asset.id == asset_id).first()

    def get_by_id_or_404(self, asset_id: int) -> Asset:
        asset = self.get_by_id(asset_id)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset with id {asset_id} not found",
            )
        return asset

    def list_assets(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        asset_type: Optional[AssetType] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Asset], int]:
        query = self.db.query(Asset).filter(Asset.project_id == project_id)
        if asset_type:
            query = query.filter(Asset.type == asset_type)
        if search:
            query = query.filter(Asset.name.ilike(f"%{search}%"))
        total = query.count()
        assets = query.order_by(Asset.id.asc()).offset(skip).limit(limit).all()
        return assets, total

    def create(self, project_id: int, asset_data: AssetCreate) -> Asset:
        asset = Asset(project_id=project_id, **asset_data.model_dump())
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update(self, asset_id: int, update_data: AssetUpdate) -> Asset:
        asset = self.get_by_id_or_404(asset_id)
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset_id: int) -> None:
        asset = self.get_by_id_or_404(asset_id)
        self.db.delete(asset)
        self.db.commit()
```

- [ ] **Step 3: 验证 import**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "
from app.schemas.asset import AssetCreate, AssetResponse
from app.services.asset_service import AssetService
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
git add app/schemas/asset.py app/services/asset_service.py
git commit -m "feat: 添加资产 Schema 和 Service"
```

---

## Task 7: 分镜 Schema + Service

**Files:**
- Create: `app/schemas/storyboard.py`
- Create: `app/services/storyboard_service.py`

- [ ] **Step 1: 创建分镜 Schema**

创建 `app/schemas/storyboard.py`：

```python
"""Pydantic schemas for Storyboard."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.storyboard import CompositionType, CameraMovement, CameraAngle


class StoryboardShotBase(BaseModel):
    script_scene_id: int = Field(..., description="关联剧本场景 ID")
    shot_number: str = Field(..., max_length=50, description="镜头编号")
    order_index: int = Field(default=0, description="排序")
    composition: CompositionType = Field(default=CompositionType.MEDIUM, description="景别")
    camera_movement: CameraMovement = Field(default=CameraMovement.FIXED, description="运镜")
    camera_angle: CameraAngle = Field(default=CameraAngle.EYE_LEVEL, description="角度")
    visual_description: Optional[str] = Field(None, description="画面描述")
    duration_seconds: int = Field(default=5, ge=1, le=300, description="预估时长(秒)")
    key_frame_url: Optional[str] = Field(None, max_length=500, description="关键帧图")
    character_ids: Optional[list[int]] = Field(None, description="出场人物资产ID")
    prop_ids: Optional[list[int]] = Field(None, description="道具资产ID")


class StoryboardShotCreate(StoryboardShotBase):
    pass


class StoryboardShotUpdate(BaseModel):
    script_scene_id: Optional[int] = None
    shot_number: Optional[str] = Field(None, max_length=50)
    order_index: Optional[int] = None
    composition: Optional[CompositionType] = None
    camera_movement: Optional[CameraMovement] = None
    camera_angle: Optional[CameraAngle] = None
    visual_description: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=1, le=300)
    key_frame_url: Optional[str] = Field(None, max_length=500)
    character_ids: Optional[list[int]] = None
    prop_ids: Optional[list[int]] = None


class StoryboardShotResponse(StoryboardShotBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderRequest(BaseModel):
    shot_ids: list[int] = Field(..., description="排序后的镜头ID列表")
```

- [ ] **Step 2: 创建分镜 Service**

创建 `app/services/storyboard_service.py`：

```python
"""Storyboard service - business logic for storyboard management."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.storyboard import StoryboardShot
from app.schemas.storyboard import StoryboardShotCreate, StoryboardShotUpdate


class StoryboardService:
    """Service for managing project storyboards."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, shot_id: int) -> Optional[StoryboardShot]:
        return self.db.query(StoryboardShot).filter(StoryboardShot.id == shot_id).first()

    def get_by_id_or_404(self, shot_id: int) -> StoryboardShot:
        shot = self.get_by_id(shot_id)
        if not shot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Storyboard shot with id {shot_id} not found",
            )
        return shot

    def list_shots(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[StoryboardShot], int]:
        query = self.db.query(StoryboardShot).filter(StoryboardShot.project_id == project_id)
        total = query.count()
        shots = query.order_by(StoryboardShot.order_index.asc()).offset(skip).limit(limit).all()
        return shots, total

    def create(self, project_id: int, shot_data: StoryboardShotCreate) -> StoryboardShot:
        shot = StoryboardShot(project_id=project_id, **shot_data.model_dump())
        self.db.add(shot)
        self.db.commit()
        self.db.refresh(shot)
        return shot

    def update(self, shot_id: int, update_data: StoryboardShotUpdate) -> StoryboardShot:
        shot = self.get_by_id_or_404(shot_id)
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(shot, field, value)
        self.db.commit()
        self.db.refresh(shot)
        return shot

    def delete(self, shot_id: int) -> None:
        shot = self.get_by_id_or_404(shot_id)
        self.db.delete(shot)
        self.db.commit()

    def reorder(self, project_id: int, shot_ids: list[int]) -> list[StoryboardShot]:
        """Reorder shots by the given ID list."""
        shots = (
            self.db.query(StoryboardShot)
            .filter(
                StoryboardShot.project_id == project_id,
                StoryboardShot.id.in_(shot_ids),
            )
            .all()
        )
        shot_map = {s.id: s for s in shots}
        for idx, shot_id in enumerate(shot_ids):
            if shot_id in shot_map:
                shot_map[shot_id].order_index = idx
        self.db.commit()
        return self.list_shots(project_id, skip=0, limit=len(shot_ids))[0]
```

- [ ] **Step 3: 验证 import**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "
from app.schemas.storyboard import StoryboardShotCreate, StoryboardShotResponse
from app.services.storyboard_service import StoryboardService
print('OK')
"
```
Expected: `OK`

- [ ] **Step 4: 提交**

```bash
git add app/schemas/storyboard.py app/services/storyboard_service.py
git commit -m "feat: 添加分镜 Schema 和 Service"
```

---

## Task 8: API Router + deps + 路由注册

**Files:**
- Create: `app/api/v1/assets.py`
- Create: `app/api/v1/storyboard.py`
- Modify: `app/api/deps.py`
- Modify: `app/api/v1/router.py`

- [ ] **Step 1: 在 deps.py 中添加两个依赖**

在 `app/api/deps.py` 末尾添加：

```python
from app.services.asset_service import AssetService
from app.services.storyboard_service import StoryboardService

def get_asset_service(db: DBSession) -> AssetService:
    return AssetService(db)

def get_storyboard_service(db: DBSession) -> StoryboardService:
    return StoryboardService(db)

AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
StoryboardServiceDep = Annotated[StoryboardService, Depends(get_storyboard_service)]
```

- [ ] **Step 2: 创建资产 API Router**

创建 `app/api/v1/assets.py`：

```python
"""Asset management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import AssetServiceDep
from app.models.asset import AssetType
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter()


@router.get("", summary="获取项目资产列表")
def list_assets(
    project_id: int = Query(..., description="项目 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type_filter: AssetType | None = Query(None, alias="type", description="按类型筛选"),
    search: str | None = Query(None, description="按名称搜索"),
    service: AssetServiceDep = ...,
):
    skip = (page - 1) * page_size
    assets, total = service.list_assets(
        project_id=project_id,
        skip=skip,
        limit=page_size,
        asset_type=type_filter,
        search=search,
    )
    return {
        "items": assets,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{asset_id}", response_model=AssetResponse, summary="获取资产详情")
def get_asset(asset_id: int, service: AssetServiceDep):
    return service.get_by_id_or_404(asset_id)


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED, summary="创建资产")
def create_asset(
    asset_data: AssetCreate,
    project_id: int = Query(..., description="项目 ID"),
    service: AssetServiceDep = ...,
):
    return service.create(project_id=project_id, asset_data=asset_data)


@router.put("/{asset_id}", response_model=AssetResponse, summary="更新资产")
def update_asset(asset_id: int, update_data: AssetUpdate, service: AssetServiceDep):
    return service.update(asset_id, update_data)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除资产")
def delete_asset(asset_id: int, service: AssetServiceDep):
    service.delete(asset_id)
```

- [ ] **Step 3: 创建分镜 API Router**

创建 `app/api/v1/storyboard.py`：

```python
"""Storyboard management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import StoryboardServiceDep
from app.schemas.storyboard import (
    ReorderRequest,
    StoryboardShotCreate,
    StoryboardShotResponse,
    StoryboardShotUpdate,
)

router = APIRouter()


@router.get("", summary="获取项目分镜列表")
def list_storyboard_shots(
    project_id: int = Query(..., description="项目 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    service: StoryboardServiceDep = ...,
):
    skip = (page - 1) * page_size
    shots, total = service.list_shots(
        project_id=project_id,
        skip=skip,
        limit=page_size,
    )
    return {
        "items": shots,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{shot_id}", response_model=StoryboardShotResponse, summary="获取分镜详情")
def get_storyboard_shot(shot_id: int, service: StoryboardServiceDep):
    return service.get_by_id_or_404(shot_id)


@router.post("", response_model=StoryboardShotResponse, status_code=status.HTTP_201_CREATED, summary="创建分镜")
def create_storyboard_shot(
    shot_data: StoryboardShotCreate,
    project_id: int = Query(..., description="项目 ID"),
    service: StoryboardServiceDep = ...,
):
    return service.create(project_id=project_id, shot_data=shot_data)


@router.put("/{shot_id}", response_model=StoryboardShotResponse, summary="更新分镜")
def update_storyboard_shot(
    shot_id: int,
    update_data: StoryboardShotUpdate,
    service: StoryboardServiceDep,
):
    return service.update(shot_id, update_data)


@router.delete("/{shot_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除分镜")
def delete_storyboard_shot(shot_id: int, service: StoryboardServiceDep):
    service.delete(shot_id)


@router.post("/reorder", summary="重排分镜顺序")
def reorder_storyboard(
    reorder_data: ReorderRequest,
    project_id: int = Query(..., description="项目 ID"),
    service: StoryboardServiceDep = ...,
):
    return service.reorder(project_id=project_id, shot_ids=reorder_data.shot_ids)
```

- [ ] **Step 4: 在 router.py 中注册新路由**

在 `app/api/v1/router.py` 中添加导入：
```python
from app.api.v1 import assets as assets_router
from app.api.v1 import storyboard as storyboard_router
```

在 `projects_router` 之后添加：
```python
api_router.include_router(assets_router.router, prefix="/assets", tags=["资产管理"])
api_router.include_router(storyboard_router.router, prefix="/storyboard", tags=["分镜管理"])
```

- [ ] **Step 5: 验证 API 启动**

```bash
cd D:/code/ShortDram-Studio/backend && python -c "
from app.main import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
new_routes = [r for r in routes if 'asset' in r or 'storyboard' in r]
print('New routes:', sorted(new_routes))
"
```
Expected: 输出 assets 和 storyboard 相关路由

- [ ] **Step 6: 提交**

```bash
git add app/api/v1/assets.py app/api/v1/storyboard.py app/api/deps.py app/api/v1/router.py
git commit -m "feat: 实现资产和分镜 CRUD API"
```

---

## Task 9: 编写测试

**Files:**
- Create: `tests/test_project_phase.py`
- Create: `tests/test_assets.py`
- Create: `tests/test_storyboard.py`

- [ ] **Step 1: 查看现有测试结构和 fixture**

```bash
cat D:/code/ShortDram-Studio/backend/tests/conftest.py
```
确认 client 和 db_session fixture 的用法。

- [ ] **Step 2: 编写项目阶段流转测试**

创建 `tests/test_project_phase.py`：

```python
"""Tests for project phase transitions."""


def test_new_project_has_script_phase(client):
    resp = client.post("/api/v1/projects", json={"name": "测试项目"})
    assert resp.status_code == 201
    assert resp.json()["phase"] == "script"


def test_transition_phase_forward(client):
    resp = client.post("/api/v1/projects", json={"name": "推进测试"})
    pid = resp.json()["id"]

    for phase in ["asset", "storyboard", "video", "completed"]:
        r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": phase})
        assert r.status_code == 200
        assert r.json()["phase"] == phase


def test_transition_phase_backward(client):
    resp = client.post("/api/v1/projects", json={"name": "回退测试"})
    pid = resp.json()["id"]

    client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "video"})
    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "asset"})
    assert r.status_code == 200
    assert r.json()["phase"] == "asset"


def test_completed_phase_updates_status(client):
    resp = client.post("/api/v1/projects", json={"name": "完成测试"})
    pid = resp.json()["id"]
    assert resp.json()["status"] == "draft"

    r = client.post(f"/api/v1/projects/{pid}/phase", json={"target_phase": "completed"})
    assert r.json()["phase"] == "completed"
    assert r.json()["status"] == "completed"
```

- [ ] **Step 3: 编写资产 API 测试**

创建 `tests/test_assets.py`：

```python
"""Tests for asset management API."""


def _create_project(client):
    resp = client.post("/api/v1/projects", json={"name": "资产测试项目"})
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_character_asset(client):
    pid = _create_project(client)
    resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={
            "type": "character",
            "name": "男主角",
            "description": "25岁都市青年",
            "metadata": {"age": "25", "gender": "男"},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "男主角"
    assert data["type"] == "character"
    assert data["source"] == "manual"
    assert data["reference_count"] == 0
    assert data["metadata"]["age"] == "25"


def test_list_assets_filter_and_search(client):
    pid = _create_project(client)
    for i in range(3):
        client.post(f"/api/v1/assets?project_id={pid}", json={"type": "character", "name": f"角色{i}"})
    client.post(f"/api/v1/assets?project_id={pid}", json={"type": "scene", "name": "办公室"})

    # all
    r = client.get(f"/api/v1/assets?project_id={pid}")
    assert r.status_code == 200
    assert r.json()["total"] == 4

    # type filter
    r = client.get(f"/api/v1/assets?project_id={pid}&type=character")
    assert r.json()["total"] == 3

    # search
    r = client.get(f"/api/v1/assets?project_id={pid}&search=办公室")
    assert r.json()["total"] == 1


def test_get_update_delete_asset(client):
    pid = _create_project(client)
    create_resp = client.post(
        f"/api/v1/assets?project_id={pid}",
        json={"type": "prop", "name": "道具A"},
    )
    aid = create_resp.json()["id"]

    # get
    r = client.get(f"/api/v1/assets/{aid}")
    assert r.status_code == 200
    assert r.json()["name"] == "道具A"

    # update
    r = client.put(f"/api/v1/assets/{aid}", json={"name": "道具B", "image_url": "http://img"})
    assert r.status_code == 200
    assert r.json()["name"] == "道具B"
    assert r.json()["image_url"] == "http://img"

    # delete
    r = client.delete(f"/api/v1/assets/{aid}")
    assert r.status_code == 204

    # verify deleted
    r = client.get(f"/api/v1/assets/{aid}")
    assert r.status_code == 404


def test_nonexistent_asset_404(client):
    r = client.get("/api/v1/assets/99999")
    assert r.status_code == 404
```

- [ ] **Step 4: 编写分镜 API 测试**

创建 `tests/test_storyboard.py`：

```python
"""Tests for storyboard management API."""

from app.models.script import Script, ScriptScene


def _create_project_with_scene(client, db_session):
    resp = client.post("/api/v1/projects", json={"name": "分镜测试项目"})
    pid = resp.json()["id"]

    script = Script(project_id=pid, title="测试剧本", total_episodes=1)
    db_session.add(script)
    db_session.flush()

    scene = ScriptScene(
        script_id=script.id,
        scene_number="1",
        location="办公室",
        int_ext="INT",
        time_of_day="日",
        description="主角走进办公室",
        order_index=0,
    )
    db_session.add(scene)
    db_session.commit()
    return pid, scene.id


def test_create_storyboard_shot(client, db_session):
    pid, scene_id = _create_project_with_scene(client, db_session)

    resp = client.post(
        f"/api/v1/storyboard?project_id={pid}",
        json={
            "script_scene_id": scene_id,
            "shot_number": "S01E01-001",
            "composition": "中景",
            "camera_movement": "固定",
            "camera_angle": "平视",
            "visual_description": "主角走进办公室",
            "duration_seconds": 5,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["shot_number"] == "S01E01-001"
    assert data["composition"] == "中景"
    assert data["duration_seconds"] == 5
    assert data["project_id"] == pid


def test_list_storyboard_shots(client, db_session):
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot
    for i in range(3):
        db_session.add(StoryboardShot(
            project_id=pid, script_scene_id=scene_id,
            shot_number=f"S01E01-00{i+1}", order_index=i,
        ))
    db_session.commit()

    r = client.get(f"/api/v1/storyboard?project_id={pid}")
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert len(r.json()["items"]) == 3


def test_update_storyboard_shot(client, db_session):
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot
    shot = StoryboardShot(project_id=pid, script_scene_id=scene_id, shot_number="S01E01-001", order_index=0)
    db_session.add(shot)
    db_session.commit()

    r = client.put(
        f"/api/v1/storyboard/{shot.id}",
        json={"composition": "特写", "duration_seconds": 10, "visual_description": "新描述"},
    )
    assert r.status_code == 200
    assert r.json()["composition"] == "特写"
    assert r.json()["duration_seconds"] == 10


def test_delete_storyboard_shot(client, db_session):
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot
    shot = StoryboardShot(project_id=pid, script_scene_id=scene_id, shot_number="S01E01-001", order_index=0)
    db_session.add(shot)
    db_session.commit()

    r = client.delete(f"/api/v1/storyboard/{shot.id}")
    assert r.status_code == 204

    r = client.get(f"/api/v1/storyboard/{shot.id}")
    assert r.status_code == 404


def test_reorder_storyboard_shots(client, db_session):
    pid, scene_id = _create_project_with_scene(client, db_session)

    from app.models.storyboard import StoryboardShot
    shots = []
    for i in range(3):
        s = StoryboardShot(project_id=pid, script_scene_id=scene_id, shot_number=f"S{i+1}", order_index=i)
        db_session.add(s)
        shots.append(s)
    db_session.commit()

    # reverse order
    new_order = [s.id for s in reversed(shots)]
    r = client.post(
        f"/api/v1/storyboard/reorder?project_id={pid}",
        json={"shot_ids": new_order},
    )
    assert r.status_code == 200

    # verify order
    r = client.get(f"/api/v1/storyboard?project_id={pid}")
    items = r.json()["items"]
    assert items[0]["id"] == new_order[0]
    assert items[1]["id"] == new_order[1]
    assert items[2]["id"] == new_order[2]
```

- [ ] **Step 5: 运行所有测试**

```bash
cd D:/code/ShortDram-Studio/backend && python -m pytest tests/test_project_phase.py tests/test_assets.py tests/test_storyboard.py -v
```
Expected: 全部通过

- [ ] **Step 6: 修复任何失败**

如果有测试失败，根据错误信息修复代码，直到全部通过。

- [ ] **Step 7: 提交**

```bash
git add tests/test_project_phase.py tests/test_assets.py tests/test_storyboard.py
git commit -m "test: 添加阶段流转/资产/分镜 API 测试"
```

---

## Task 10: 全量测试验证 + 收尾

- [ ] **Step 1: 运行全量测试**

```bash
cd D:/code/ShortDram-Studio/backend && python -m pytest tests/ -v
```
Expected: 所有测试通过

- [ ] **Step 2: 运行 Alembic 降级再升级验证迁移**

```bash
cd D:/code/ShortDram-Studio/backend && alembic downgrade -1 && alembic upgrade head
```
Expected: 降级和升级都成功

- [ ] **Step 3: 检查 git 提交历史**

```bash
cd D:/code/ShortDram-Studio && git log --oneline -10
```

- [ ] **Step 4: 最终提交（如有遗漏）**

确保所有改动都已提交。
