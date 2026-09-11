"""MCP server service."""
import json
import time
from typing import Any, List, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.mcp import Mcp
from app.schemas.mcp import (
    McpCreate,
    McpTestConnectionResponse,
    McpUpdate,
)


def mask_secrets(secrets: dict | None) -> dict | None:
    """Mask secret values with '***' for safe display.

    Only top-level keys are preserved; values are replaced with '***' if truthy,
    None stays None.
    """
    if not secrets:
        return secrets
    masked = {}
    for key, val in secrets.items():
        if isinstance(val, (dict, list)):
            masked[key] = "***"
        elif val is None:
            masked[key] = None
        else:
            masked[key] = "***"
    return masked


class McpService:
    """Service for managing MCP servers."""

    def __init__(self, db: Session):
        self.db = db

    # ── CRUD ──────────────────────────────────────────────

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
        mcp_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Mcp], int]:
        query = self.db.query(Mcp)
        if is_enabled is not None:
            query = query.filter(Mcp.is_enabled == is_enabled)  # noqa: E712
        if mcp_type:
            query = query.filter(Mcp.mcp_type == mcp_type)
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
            mcp_type=data.mcp_type,
            config=data.config,
            secrets=data.secrets,
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

    # ── Connection testing ────────────────────────────────

    def test_connection(
        self,
        url: str,
        transport: str = "streamable_http",
        config: dict | None = None,
        secrets: dict | None = None,
    ) -> McpTestConnectionResponse:
        """Test MCP server connection and list available tools.

        Performs a JSON-RPC `tools/list` call to validate the connection.
        """
        start = time.time()
        try:
            headers = {"Content-Type": "application/json"}
            timeout = 10.0

            # Merge config headers with secrets-based auth
            if config and config.get("headers"):
                for k, v in config["headers"].items():
                    headers[k] = v

            if secrets:
                # Support common auth patterns from secrets
                if secrets.get("api_key") and secrets.get("api_key_header"):
                    headers[secrets["api_key_header"]] = (
                        f"Bearer {secrets['api_key']}"
                        if secrets.get("api_key_prefix") == "bearer"
                        else secrets["api_key"]
                    )
                elif secrets.get("api_key"):
                    headers["x-api-key"] = secrets["api_key"]
                if secrets.get("bearer_token"):
                    headers["Authorization"] = f"Bearer {secrets['bearer_token']}"

            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }

            if transport == "stdio":
                return McpTestConnectionResponse(
                    ok=False,
                    error="stdio transport testing not supported over HTTP",
                )

            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload, headers=headers)

            latency = round((time.time() - start) * 1000, 1)

            if resp.status_code != 200:
                return McpTestConnectionResponse(
                    ok=False,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    latency_ms=latency,
                )

            try:
                data = resp.json()
            except json.JSONDecodeError:
                return McpTestConnectionResponse(
                    ok=False,
                    error=f"Invalid JSON response: {resp.text[:200]}",
                    latency_ms=latency,
                )

            if "error" in data:
                err = data["error"]
                msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                return McpTestConnectionResponse(
                    ok=False,
                    error=msg[:300],
                    latency_ms=latency,
                )

            tools = data.get("result", {}).get("tools", [])
            server_version = data.get("result", {}).get("serverInfo", {}).get("version")

            return McpTestConnectionResponse(
                ok=True,
                tools=tools,
                server_version=server_version,
                latency_ms=latency,
            )

        except httpx.TimeoutException:
            return McpTestConnectionResponse(
                ok=False,
                error="连接超时",
                latency_ms=round((time.time() - start) * 1000, 1),
            )
        except Exception as exc:  # noqa: BLE001
            return McpTestConnectionResponse(
                ok=False,
                error=str(exc)[:300],
                latency_ms=round((time.time() - start) * 1000, 1),
            )

    def refresh_tools(self, mcp_id: int) -> List[dict[str, Any]]:
        """Refresh the cached tools list for an MCP server.

        Returns the new tools list.
        """
        mcp = self.get_by_id_or_404(mcp_id)
        result = self.test_connection(
            url=mcp.url,
            transport=mcp.transport,
            config=mcp.config,
            secrets=mcp.secrets,
        )
        if not result.ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"连接失败: {result.error}",
            )
        mcp.tools = result.tools or []
        self.db.commit()
        self.db.refresh(mcp)
        return mcp.tools or []
