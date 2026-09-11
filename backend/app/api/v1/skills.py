"""Skill management endpoints."""
import json

from fastapi import APIRouter, File, Query, UploadFile, status

from app.api.deps import SkillServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.skill import (
    SkillCreate,
    SkillImportRequest,
    SkillImportResult,
    SkillImportTextRequest,
    SkillResponse,
    SkillUpdate,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SkillResponse], summary="获取 Skill 列表")
def list_skills(
    service: SkillServiceDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_enabled: bool | None = None,
    search: str | None = None,
):
    skills, total = service.list_skills(
        skip=(page - 1) * page_size,
        limit=page_size,
        is_enabled=is_enabled,
        search=search,
    )
    return PaginatedResponse(
        items=skills,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{skill_id}", response_model=SkillResponse, summary="获取 Skill 详情")
def get_skill(skill_id: int, service: SkillServiceDep):
    return service.get_by_id_or_404(skill_id)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED, summary="创建 Skill")
def create_skill(data: SkillCreate, service: SkillServiceDep):
    return service.create(data)


@router.put("/{skill_id}", response_model=SkillResponse, summary="更新 Skill")
def update_skill(skill_id: int, data: SkillUpdate, service: SkillServiceDep):
    return service.update(skill_id, data)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除 Skill")
def delete_skill(skill_id: int, service: SkillServiceDep):
    service.delete(skill_id)


@router.post(
    "/import/text",
    response_model=SkillImportResult,
    summary="从文本导入 Skill",
)
def import_skill_from_text(data: SkillImportTextRequest, service: SkillServiceDep):
    """Import a single skill from raw text.

    Supports auto-parsing of:
    - Markdown (# Title + description + content)
    - YAML front matter
    - Plain text (first line = name)
    """
    return service.import_from_text(
        text=data.text,
        name=data.name,
        description=data.description,
        overwrite=data.overwrite,
    )


@router.post(
    "/import/batch",
    response_model=SkillImportResult,
    summary="批量导入 Skill",
)
def import_skills_batch(data: SkillImportRequest, service: SkillServiceDep):
    """Batch import multiple skills from structured JSON."""
    return service.import_batch(items=data.skills, overwrite=data.overwrite)


@router.post(
    "/import/file",
    response_model=SkillImportResult,
    summary="从文件导入 Skill",
)
async def import_skill_from_file(
    service: SkillServiceDep,
    file: UploadFile = File(..., description=".md / .txt / .json 文件"),
    overwrite: bool = Query(False, description="是否覆盖同名 Skill"),
):
    """Import skills from an uploaded file.

    Supported formats:
    - `.md` / `.txt`: Single skill (auto-parsed)
    - `.json`: Array of skill objects for batch import
    """
    content = await file.read()
    filename = (file.filename or "").lower()

    # Try to decode as text
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk", errors="ignore")

    # JSON file: batch import
    if filename.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            return SkillImportResult(
                total=0,
                errors=[f"JSON 解析失败: {e}"],
            )

        items = []
        if isinstance(data, list):
            raw_items = data
        elif isinstance(data, dict) and "skills" in data and isinstance(data["skills"], list):
            raw_items = data["skills"]
        else:
            raw_items = [data]

        from app.schemas.skill import SkillImportItem

        for raw in raw_items:
            try:
                item = SkillImportItem(**raw)
                items.append(item)
            except Exception:
                # Skip invalid items
                pass

        return service.import_batch(items=items, overwrite=overwrite)

    # Markdown / text file: single skill import
    # Use filename (without extension) as hint for the name
    import os

    base_name = os.path.splitext(file.filename or "")[0]
    return service.import_from_text(
        text=text,
        name=base_name if base_name else None,
        overwrite=overwrite,
    )
