"""Skill management endpoints."""
from fastapi import APIRouter, Query, status

from app.api.deps import SkillServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate

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
