"""Skill service."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate


class SkillService:
    """Service for managing skills."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, skill_id: int) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.id == skill_id).first()

    def get_by_id_or_404(self, skill_id: int) -> Skill:
        skill = self.get_by_id(skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill with id {skill_id} not found",
            )
        return skill

    def list_skills(
        self,
        skip: int = 0,
        limit: int = 100,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Skill], int]:
        query = self.db.query(Skill)
        if is_enabled is not None:
            query = query.filter(Skill.is_enabled == is_enabled)  # noqa: E712
        if search:
            pattern = f"%{search}%"
            query = query.filter(Skill.name.ilike(pattern) | Skill.description.ilike(pattern))
        total = query.count()
        skills = query.order_by(Skill.created_at.desc()).offset(skip).limit(limit).all()
        return skills, total

    def create(self, data: SkillCreate) -> Skill:
        if self.db.query(Skill).filter(Skill.name == data.name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Skill with name '{data.name}' already exists",
            )
        skill = Skill(
            name=data.name,
            description=data.description,
            content=data.content,
            is_enabled=data.is_enabled,
        )
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def update(self, skill_id: int, data: SkillUpdate) -> Skill:
        skill = self.get_by_id_or_404(skill_id)
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != skill.name:
            if self.db.query(Skill).filter(Skill.name == update_data["name"]).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Skill with name '{update_data['name']}' already exists",
                )
        for field, value in update_data.items():
            setattr(skill, field, value)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def delete(self, skill_id: int) -> None:
        skill = self.get_by_id_or_404(skill_id)
        self.db.delete(skill)
        self.db.commit()
