"""MCP server service."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.mcp import Mcp
from app.schemas.mcp import McpCreate, McpUpdate


class McpService:
    """Service for managing MCP servers."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, mcp_id: int) -> Optional[Mcp]:
        return self.db.query(Mcp).filter(Mcp.id == mcp_id).first()

    def get_by_id_or_404(self, mcp_id: int) -> Mcp:
        mcp = self.get_by_id(mcp_id)
        if not mcp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MCP server with id {mcp_id} not found",
            )
        return mcp

    def list_mcps(
        self,
        skip: int = 0,
        limit: int = 100,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Mcp], int]:
        query = self.db.query(Mcp)
        if is_enabled is not None:
            query = query.filter(Mcp.is_enabled == is_enabled)  # noqa: E712
        if search:
            pattern = f"%{search}%"
            query = query.filter(Mcp.name.ilike(pattern) | Mcp.description.ilike(pattern))
        total = query.count()
        mcps = query.order_by(Mcp.created_at.desc()).offset(skip).limit(limit).all()
        return mcps, total

    def create(self, data: McpCreate) -> Mcp:
        if self.db.query(Mcp).filter(Mcp.name == data.name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MCP server with name '{data.name}' already exists",
            )
        mcp = Mcp(
            name=data.name,
            url=data.url,
            transport=data.transport,
            config=data.config,
            description=data.description,
            is_enabled=data.is_enabled,
        )
        self.db.add(mcp)
        self.db.commit()
        self.db.refresh(mcp)
        return mcp

    def update(self, mcp_id: int, data: McpUpdate) -> Mcp:
        mcp = self.get_by_id_or_404(mcp_id)
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != mcp.name:
            if self.db.query(Mcp).filter(Mcp.name == update_data["name"]).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"MCP server with name '{update_data['name']}' already exists",
                )
        for field, value in update_data.items():
            setattr(mcp, field, value)
        self.db.commit()
        self.db.refresh(mcp)
        return mcp

    def delete(self, mcp_id: int) -> None:
        mcp = self.get_by_id_or_404(mcp_id)
        self.db.delete(mcp)
        self.db.commit()
