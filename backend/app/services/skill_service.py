"""Skill service."""
import re
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import (
    SkillCreate,
    SkillImportItem,
    SkillImportResult,
    SkillUpdate,
)


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

    # ── Import ─────────────────────────────────────────────

    def parse_skill_from_text(self, text: str) -> Tuple[str, Optional[str], str]:
        """Parse skill name, description, and content from raw text.

        Supports multiple formats:
        1. Markdown with H1 title + optional description paragraph
           # Skill Name
           Optional description line(s)
           
           ## Content
           ...actual content...

        2. Simple: first line as name, rest as content

        3. YAML front matter style:
           ---
           name: My Skill
           description: ...
           ---
           content body
        """
        text = text.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skill 内容不能为空",
            )

        name: Optional[str] = None
        description: Optional[str] = None
        content = text

        # Format 3: YAML front matter
        if text.startswith("---"):
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
            if match:
                fm_text = match.group(1)
                body = match.group(2)
                fm = {}
                for line in fm_text.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip().lower()] = v.strip().strip('"').strip("'")
                if "name" in fm:
                    name = fm["name"][:100]
                if "description" in fm:
                    description = fm["description"][:500]
                content = body.strip()

        # Format 1: Markdown H1
        if not name:
            lines = text.split("\n")
            if lines and lines[0].startswith("# "):
                name = lines[0][2:].strip()[:100]
                rest_lines = lines[1:]
                # Skip optional blank lines
                i = 0
                while i < len(rest_lines) and rest_lines[i].strip() == "":
                    i += 1
                # Try to find description (paragraph before first heading or code block)
                desc_lines = []
                j = i
                while j < len(rest_lines) and rest_lines[j].strip() and not rest_lines[j].startswith("#") and not rest_lines[j].startswith("```"):
                    desc_lines.append(rest_lines[j].strip())
                    j += 1
                if desc_lines:
                    description = " ".join(desc_lines)[:500]
                content = "\n".join(rest_lines).strip()

        # Format 2: First line as name
        if not name:
            lines = text.split("\n")
            name = lines[0].strip()[:100]
            if len(lines) > 1:
                content = "\n".join(lines[1:]).strip()
            else:
                content = name  # Fallback: whole text is both name and content

        if not name:
            name = "Untitled Skill"
        if not content:
            content = name

        return name, description, content

    def import_from_text(
        self,
        text: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> SkillImportResult:
        """Import a single skill from raw text.

        Args:
            text: Raw skill content text.
            name: Optional explicit name (overrides parsed name).
            description: Optional explicit description.
            overwrite: Whether to overwrite existing skill with same name.

        Returns:
            Import result summary.
        """
        parsed_name, parsed_desc, content = self.parse_skill_from_text(text)
        final_name = (name or parsed_name)[:100]
        final_desc = (description or parsed_desc)[:500] if description or parsed_desc else None

        result = SkillImportResult(total=1)

        existing = self.db.query(Skill).filter(Skill.name == final_name).first()
        if existing:
            if not overwrite:
                result.skipped = 1
                result.errors.append(f"Skill '{final_name}' 已存在，跳过")
                return result
            # Update existing
            existing.description = final_desc
            existing.content = content
            self.db.commit()
            self.db.refresh(existing)
            result.updated = 1
            result.imported_ids.append(existing.id)
        else:
            skill = Skill(
                name=final_name,
                description=final_desc,
                content=content,
                is_enabled=True,
            )
            self.db.add(skill)
            self.db.commit()
            self.db.refresh(skill)
            result.created = 1
            result.imported_ids.append(skill.id)

        return result

    def import_batch(
        self,
        items: List[SkillImportItem],
        overwrite: bool = False,
    ) -> SkillImportResult:
        """Batch import multiple skills.

        Args:
            items: List of skill items to import.
            overwrite: Whether to overwrite existing skills with same name.

        Returns:
            Import result summary.
        """
        result = SkillImportResult(total=len(items))

        for item in items:
            try:
                name = item.name.strip()[:100]
                description = (item.description or "").strip()[:500] or None
                content = item.content.strip()

                if not name:
                    result.errors.append("Skill 名称不能为空，跳过")
                    result.skipped += 1
                    continue
                if not content:
                    result.errors.append(f"Skill '{name}' 内容不能为空，跳过")
                    result.skipped += 1
                    continue

                existing = self.db.query(Skill).filter(Skill.name == name).first()
                if existing:
                    if not overwrite:
                        result.skipped += 1
                        result.errors.append(f"Skill '{name}' 已存在，跳过")
                        continue
                    existing.description = description
                    existing.content = content
                    if item.is_enabled is not None:
                        existing.is_enabled = item.is_enabled
                    self.db.commit()
                    self.db.refresh(existing)
                    result.updated += 1
                    result.imported_ids.append(existing.id)
                else:
                    skill = Skill(
                        name=name,
                        description=description,
                        content=content,
                        is_enabled=item.is_enabled if item.is_enabled is not None else True,
                    )
                    self.db.add(skill)
                    self.db.commit()
                    self.db.refresh(skill)
                    result.created += 1
                    result.imported_ids.append(skill.id)

            except Exception as e:  # noqa: BLE001
                result.skipped += 1
                result.errors.append(f"Skill '{item.name}' 导入失败: {e}")

        return result
