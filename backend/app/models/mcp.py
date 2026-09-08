"""MCP (Model Context Protocol) server model."""
from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Mcp(BaseModel):
    """A Model Context Protocol server that can be bound to agents.

    Attributes:
        name: Unique display name.
        url: Server endpoint (SSE or streamable HTTP).
        transport: Transport type (streamable_http / sse / stdio).
        config: Optional JSON configuration (headers, auth, etc.).
        description: Optional description.
        is_enabled: Whether the MCP server is active.
    """

    __tablename__ = "mcps"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    transport: Mapped[str] = mapped_column(String(50), default="streamable_http", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<Mcp(id={self.id}, name='{self.name}')>"
