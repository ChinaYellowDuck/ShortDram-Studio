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
