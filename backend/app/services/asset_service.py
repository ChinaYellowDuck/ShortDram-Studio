"""Asset service - business logic for asset management."""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType
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
