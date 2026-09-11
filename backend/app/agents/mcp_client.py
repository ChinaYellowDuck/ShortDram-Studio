"""MCP (Model Context Protocol) tool client.

Provides a lightweight client for calling tools on remote MCP servers
using the JSON-RPC based MCP protocol over HTTP / SSE transport.

This is a minimal implementation focused on tool calling functionality
needed by agents. Supports both `streamable_http` and `sse` transports.
"""
import json
import time
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class McpTool:
    """Represents a tool exposed by an MCP server."""

    def __init__(
        self,
        name: str,
        description: str = "",
        input_schema: Optional[Dict[str, Any]] = None,
        mcp_server_id: int = 0,
        mcp_server_name: str = "",
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema or {"type": "object", "properties": {}}
        self.mcp_server_id = mcp_server_id
        self.mcp_server_name = mcp_server_name

    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def __repr__(self) -> str:
        return f"<McpTool(name='{self.name}', server='{self.mcp_server_name}')>"


class McpToolClient:
    """Client for calling tools on a single MCP server.

    Usage:
        client = McpToolClient(
            url="https://mcp.example.com/sse",
            transport="sse",
            secrets={"api_key": "xxx"},
        )
        tools = client.list_tools()
        result = client.call_tool("get_weather", {"city": "Beijing"})
    """

    def __init__(
        self,
        url: str,
        transport: str = "streamable_http",
        config: Optional[Dict[str, Any]] = None,
        secrets: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        server_id: int = 0,
        server_name: str = "",
    ):
        self.url = url
        self.transport = transport
        self.config = config or {}
        self.secrets = secrets or {}
        self.timeout = self.config.get("timeout", timeout)
        self.server_id = server_id
        self.server_name = server_name
        self._client: Optional[httpx.Client] = None
        self._headers = self._build_headers()
        self._request_id = 0

    # ── Setup / teardown ────────────────────────────────────

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers from config + secrets."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Custom headers from config
        if self.config.get("headers"):
            for k, v in self.config["headers"].items():
                headers[k] = str(v)

        # API key auth
        if self.secrets.get("api_key"):
            header = self.secrets.get("api_key_header", "x-api-key")
            prefix = self.secrets.get("api_key_prefix", "none")
            if prefix == "bearer":
                headers[header] = f"Bearer {self.secrets['api_key']}"
            else:
                headers[header] = str(self.secrets["api_key"])

        # Bearer token auth
        if self.secrets.get("bearer_token"):
            headers["Authorization"] = f"Bearer {self.secrets['bearer_token']}"

        return headers

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── JSON-RPC helpers ────────────────────────────────────

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _rpc_call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a JSON-RPC call to the MCP server.

        Returns the result object from the response.
        Raises an exception if the response contains an error.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }

        client = self._get_client()
        start = time.time()

        try:
            resp = client.post(self.url, json=payload, headers=self._headers)
        except httpx.TimeoutException:
            raise RuntimeError(f"MCP server {self.server_name} timed out after {self.timeout}s")
        except httpx.HTTPError as e:
            raise RuntimeError(f"MCP server {self.server_name} HTTP error: {e}")

        latency = round((time.time() - start) * 1000, 1)

        if resp.status_code != 200:
            raise RuntimeError(
                f"MCP server {self.server_name} returned HTTP {resp.status_code}: {resp.text[:300]}"
            )

        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise RuntimeError(
                f"MCP server {self.server_name} returned invalid JSON: {resp.text[:300]}"
            )

        if "error" in data:
            err = data["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            code = err.get("code", -1) if isinstance(err, dict) else -1
            raise RuntimeError(f"MCP error [{code}]: {msg}")

        logger.debug(
            f"[MCP] {self.server_name}: {method} -> {latency}ms"
        )
        return data.get("result", {})

    # ── Tool operations ─────────────────────────────────────

    def list_tools(self) -> List[McpTool]:
        """List all tools available on this MCP server."""
        result = self._rpc_call("tools/list")
        raw_tools = result.get("tools", [])
        tools: List[McpTool] = []
        for t in raw_tools:
            tool = McpTool(
                name=t.get("name", "unknown"),
                description=t.get("description", ""),
                input_schema=t.get("inputSchema") or t.get("input_schema"),
                mcp_server_id=self.server_id,
                mcp_server_name=self.server_name,
            )
            tools.append(tool)
        return tools

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call.
            arguments: Dict of arguments to pass to the tool.

        Returns:
            Tool result (typically a dict with `content` array for MCP).

        Raises:
            RuntimeError if the call fails.
        """
        params = {"name": tool_name, "arguments": arguments}
        result = self._rpc_call("tools/call", params)
        if result.get("isError"):
            # Extract error message from content
            content = result.get("content", [])
            msg_parts = []
            for c in content:
                if c.get("type") == "text":
                    msg_parts.append(c.get("text", ""))
                else:
                    msg_parts.append(str(c))
            raise RuntimeError(f"Tool '{tool_name}' error: {'; '.join(msg_parts)}")
        return result

    def call_tool_text(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool and extract the text content from the response.

        Convenience method for tools that return text content.
        """
        result = self.call_tool(tool_name, arguments)
        content = result.get("content", [])
        texts = []
        for c in content:
            if c.get("type") == "text":
                texts.append(c.get("text", ""))
        return "\n".join(texts)
