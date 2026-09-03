"""Script management endpoints.

Handles scripts, scenes, characters, dialogues, and Fountain export.
"""
from fastapi import APIRouter, Query, status

from app.api.deps import ScriptServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.script import (
    ScriptCharacterCreate,
    ScriptCharacterResponse,
    ScriptCharacterUpdate,
    ScriptCreate,
    ScriptDetailResponse,
    ScriptDialogueCreate,
    ScriptDialogueResponse,
    ScriptDialogueUpdate,
    ScriptFountainExport,
    ScriptResponse,
    ScriptSceneCreate,
    ScriptSceneResponse,
    ScriptSceneUpdate,
    ScriptUpdate,
)

router = APIRouter()


# ── Script endpoints ────────────────────────────────────────────────────────


@router.get(
    "/project/{project_id}",
    response_model=PaginatedResponse[ScriptResponse],
    summary="获取项目剧本列表",
)
def list_scripts(
    project_id: int,
    service: ScriptServiceDep,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """List all scripts for a project with pagination."""
    skip = (page - 1) * page_size
    scripts, total = service.list_by_project(project_id, skip=skip, limit=page_size)
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=scripts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{script_id}", response_model=ScriptDetailResponse, summary="获取剧本详情（含场景和角色）")
def get_script(script_id: int, service: ScriptServiceDep):
    """Get full script detail including scenes, dialogues, and characters."""
    return service.get_detail(script_id)


@router.post(
    "",
    response_model=ScriptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建剧本",
)
def create_script(data: ScriptCreate, service: ScriptServiceDep):
    """Create a new script for a project."""
    return service.create(data)


@router.put("/{script_id}", response_model=ScriptResponse, summary="更新剧本")
def update_script(script_id: int, data: ScriptUpdate, service: ScriptServiceDep):
    """Update a script."""
    return service.update(script_id, data)


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除剧本")
def delete_script(script_id: int, service: ScriptServiceDep):
    """Delete a script and all its scenes/characters/dialogues."""
    service.delete(script_id)


# ── Fountain Export ─────────────────────────────────────────────────────────


@router.get(
    "/{script_id}/export/fountain",
    response_model=ScriptFountainExport,
    summary="导出 Fountain 格式剧本",
)
def export_fountain(script_id: int, service: ScriptServiceDep):
    """Export a script to Fountain plain text format."""
    script = service.get_by_id_or_404(script_id)
    content = service.export_fountain(script_id)
    return ScriptFountainExport(
        script_id=script_id,
        title=script.title,
        content=content,
    )


# ── Scene endpoints ─────────────────────────────────────────────────────────


@router.get(
    "/{script_id}/scenes",
    response_model=list[ScriptSceneResponse],
    summary="获取剧本所有场景",
)
def list_scenes(script_id: int, service: ScriptServiceDep):
    """List all scenes for a script, ordered by order_index."""
    return service.list_scenes(script_id)


@router.get(
    "/scenes/{scene_id}",
    response_model=ScriptSceneResponse,
    summary="获取场景详情（含对白）",
)
def get_scene(scene_id: int, service: ScriptServiceDep):
    """Get a scene with all its dialogues."""
    return service.get_scene_detail(scene_id)


@router.post(
    "/{script_id}/scenes",
    response_model=ScriptSceneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增场景",
)
def create_scene(script_id: int, data: ScriptSceneCreate, service: ScriptServiceDep):
    """Create a new scene in a script."""
    return service.create_scene(script_id, data)


@router.put(
    "/scenes/{scene_id}",
    response_model=ScriptSceneResponse,
    summary="更新场景",
)
def update_scene(scene_id: int, data: ScriptSceneUpdate, service: ScriptServiceDep):
    """Update a scene."""
    return service.update_scene(scene_id, data)


@router.delete(
    "/scenes/{scene_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除场景",
)
def delete_scene(scene_id: int, service: ScriptServiceDep):
    """Delete a scene."""
    service.delete_scene(scene_id)


# ── Character endpoints ─────────────────────────────────────────────────────


@router.get(
    "/{script_id}/characters",
    response_model=list[ScriptCharacterResponse],
    summary="获取剧本角色列表",
)
def list_characters(script_id: int, service: ScriptServiceDep):
    """List all characters in a script."""
    return service.list_characters(script_id)


@router.get(
    "/characters/{character_id}",
    response_model=ScriptCharacterResponse,
    summary="获取角色详情",
)
def get_character(character_id: int, service: ScriptServiceDep):
    """Get a character by ID."""
    return service.get_character_or_404(character_id)


@router.post(
    "/{script_id}/characters",
    response_model=ScriptCharacterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增角色",
)
def create_character(
    script_id: int, data: ScriptCharacterCreate, service: ScriptServiceDep
):
    """Create a new character in a script."""
    return service.create_character(script_id, data)


@router.put(
    "/characters/{character_id}",
    response_model=ScriptCharacterResponse,
    summary="更新角色",
)
def update_character(
    character_id: int, data: ScriptCharacterUpdate, service: ScriptServiceDep
):
    """Update a character."""
    return service.update_character(character_id, data)


@router.delete(
    "/characters/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除角色",
)
def delete_character(character_id: int, service: ScriptServiceDep):
    """Delete a character."""
    service.delete_character(character_id)


# ── Dialogue endpoints ──────────────────────────────────────────────────────


@router.get(
    "/scenes/{scene_id}/dialogues",
    response_model=list[ScriptDialogueResponse],
    summary="获取场景对白列表",
)
def list_dialogues(scene_id: int, service: ScriptServiceDep):
    """List all dialogues in a scene."""
    return service.list_dialogues(scene_id)


@router.get(
    "/dialogues/{dialogue_id}",
    response_model=ScriptDialogueResponse,
    summary="获取对白详情",
)
def get_dialogue(dialogue_id: int, service: ScriptServiceDep):
    """Get a dialogue by ID."""
    return service.get_dialogue_or_404(dialogue_id)


@router.post(
    "/scenes/{scene_id}/dialogues",
    response_model=ScriptDialogueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="新增对白",
)
def create_dialogue(
    scene_id: int, data: ScriptDialogueCreate, service: ScriptServiceDep
):
    """Create a new dialogue line in a scene."""
    return service.create_dialogue(scene_id, data)


@router.put(
    "/dialogues/{dialogue_id}",
    response_model=ScriptDialogueResponse,
    summary="更新对白",
)
def update_dialogue(
    dialogue_id: int, data: ScriptDialogueUpdate, service: ScriptServiceDep
):
    """Update a dialogue line."""
    return service.update_dialogue(dialogue_id, data)


@router.delete(
    "/dialogues/{dialogue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除对白",
)
def delete_dialogue(dialogue_id: int, service: ScriptServiceDep):
    """Delete a dialogue line."""
    service.delete_dialogue(dialogue_id)