"""Base classes and interfaces for all agents."""
import json
import time
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import StateGraph
from sqlalchemy.orm import Session

from app.agents.mcp_client import McpTool, McpToolClient


class BaseAgent(ABC):
    """Abstract base class for all agents.

    All agents should inherit from this class and implement the required methods.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        config: Optional[Dict[str, Any]] = None,
        mcp_tools: Optional[List[McpTool]] = None,
        mcp_clients: Optional[Dict[int, McpToolClient]] = None,
    ):
        """Initialize the agent.

        Args:
            llm: The language model to use.
            config: Optional agent-specific configuration.
            mcp_tools: List of MCP tools available to this agent.
            mcp_clients: Dict of MCP clients keyed by server ID (for tool calls).
        """
        self.llm = llm
        self.config = config or {}
        self.mcp_tools = mcp_tools or []
        self.mcp_clients = mcp_clients or {}
        self._graph = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable agent description."""
        ...

    @property
    def agent_key(self) -> str:
        """Business-unique key for the agent (maps to DB agent_key column).

        Defaults to `name`; subclasses can override to provide a different key.
        """
        return self.name

    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build and return the LangGraph state graph.

        Returns:
            Compiled LangGraph state graph.
        """
        ...

    @property
    def graph(self):
        """Lazy-loaded compiled graph."""
        if self._graph is None:
            self._graph = self.build_graph().compile()
        return self._graph

    # ── MCP tool helpers ────────────────────────────────────

    def get_available_mcp_tools(self) -> List[McpTool]:
        """Get all available MCP tools for this agent."""
        return self.mcp_tools

    def get_mcp_tools_as_functions(self) -> List[Dict[str, Any]]:
        """Get MCP tools in OpenAI function calling format."""
        return [t.to_openai_function() for t in self.mcp_tools]

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool by name.

        Searches through all available MCP clients to find the tool.

        Args:
            tool_name: Name of the tool to call.
            arguments: Tool arguments.

        Returns:
            Tool result.

        Raises:
            ValueError if tool is not found.
            RuntimeError if tool call fails.
        """
        # Find which server has this tool
        tool = next((t for t in self.mcp_tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"MCP tool '{tool_name}' not found in available tools")

        client = self.mcp_clients.get(tool.mcp_server_id)
        if not client:
            raise RuntimeError(f"MCP client for server '{tool.mcp_server_name}' not available")

        return client.call_tool(tool_name, arguments)

    def call_mcp_tool_text(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool and return text content."""
        result = self.call_mcp_tool(tool_name, arguments)
        if isinstance(result, dict) and "content" in result:
            texts = []
            for c in result["content"]:
                if isinstance(c, dict) and c.get("type") == "text":
                    texts.append(c.get("text", ""))
            return "\n".join(texts)
        return str(result)

    # ── Tool-use helpers ───────────────────────────────────

    def has_mcp_tools(self) -> bool:
        """Check if this agent has any MCP tools available."""
        return len(self.mcp_tools) > 0

    def build_tools_prompt_section(self) -> str:
        """Build the tools description section for the system prompt.

        Returns a formatted string describing all available MCP tools
        and how to use them. Empty string if no tools.
        """
        if not self.has_mcp_tools():
            return ""

        lines = [
            "",
            "## 可用工具",
            "",
            "你可以使用以下工具来辅助完成任务。当你需要外部信息或执行特定操作时，请主动调用工具。",
            "",
            "### 工具调用格式",
            "",
            '使用 `<tool_call>` 标签包裹 JSON 格式的工具调用，例如：',
            "",
            '```',
            '<tool_call>',
            '{',
            '  "name": "tool_name",',
            '  "arguments": {',
            '    "param1": "value1"',
            '  }',
            '}',
            '</tool_call>',
            '```',
            "",
            "每次只能调用一个工具。调用后等待工具返回结果，再继续思考。",
            "如果不需要工具，请直接输出最终答案，不要使用 `<tool_call>` 标签。",
            "",
            "### 工具列表",
            "",
        ]

        for i, tool in enumerate(self.mcp_tools, 1):
            lines.append(f"**{i}. {tool.name}**")
            if tool.description:
                lines.append(f"   描述：{tool.description}")
            if tool.input_schema and tool.input_schema.get("properties"):
                lines.append("   参数：")
                for pname, pschema in tool.input_schema["properties"].items():
                    ptype = pschema.get("type", "any")
                    pdesc = pschema.get("description", "")
                    preq = " (必填)" if tool.input_schema.get("required") and pname in tool.input_schema["required"] else ""
                    lines.append(f"   - `{pname}` ({ptype}{preq}): {pdesc}")
            lines.append("")

        lines.append("---")
        return "\n".join(lines)

    def parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse a tool call from LLM response text.

        Looks for <tool_call>...</tool_call> tags with JSON inside.
        Returns dict with 'name' and 'arguments' if found, None otherwise.
        """
        if not content:
            return None

        # Try XML-style <tool_call> tags
        match = re.search(
            r"<tool_call>(.*?)</tool_call>",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            json_str = match.group(1).strip()
            # Strip code fences if present
            json_str = re.sub(r"^```(?:json)?\s*", "", json_str)
            json_str = re.sub(r"\s*```$", "", json_str)
            try:
                data = json.loads(json_str)
                if "name" in data:
                    return {
                        "name": data["name"],
                        "arguments": data.get("arguments", data.get("params", {})),
                    }
            except json.JSONDecodeError:
                pass

        # Fallback: try to find JSON with name + arguments pattern
        json_pattern = re.search(
            r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
            content,
            re.DOTALL,
        )
        if json_pattern:
            try:
                args = json.loads(json_pattern.group(2))
                return {
                    "name": json_pattern.group(1),
                    "arguments": args,
                }
            except json.JSONDecodeError:
                pass

        return None

    def invoke_with_tools(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str] = None,
        max_iterations: int = 8,
    ) -> Dict[str, Any]:
        """Invoke LLM with MCP tool calling loop (ReAct pattern).

        Runs a loop:
        1. Call LLM with current messages
        2. Check if response contains a tool call
        3. If yes: execute the tool, append result to messages, repeat
        4. If no: return final response

        Args:
            messages: Initial message list (HumanMessage, etc.)
            system_prompt: Optional system prompt to prepend.
                If provided, tools section is auto-appended.
            max_iterations: Max tool call iterations to prevent infinite loops.

        Returns:
            Dict with:
            - content: Final response text
            - messages: Full message history
            - tool_calls: Number of tool calls made
            - tools_used: List of tool names used
        """
        if not self.has_mcp_tools():
            # No tools - just a simple LLM call
            all_msgs: List[BaseMessage] = []
            if system_prompt:
                all_msgs.append(SystemMessage(content=system_prompt))
            all_msgs.extend(messages)
            response = self.llm.invoke(all_msgs)
            return {
                "content": response.content if isinstance(response.content, str) else str(response.content),
                "messages": all_msgs + [response],
                "tool_calls": 0,
                "tools_used": [],
            }

        # Build enhanced system prompt with tools section
        tools_section = self.build_tools_prompt_section()
        enhanced_system = (system_prompt or "") + tools_section

        all_msgs: List[BaseMessage] = []
        if enhanced_system.strip():
            all_msgs.append(SystemMessage(content=enhanced_system))
        all_msgs.extend(messages)

        tool_calls_count = 0
        tools_used: List[str] = []

        for iteration in range(max_iterations):
            response = self.llm.invoke(all_msgs)
            content = response.content if isinstance(response.content, str) else str(response.content)

            tool_call = self.parse_tool_call(content)

            if not tool_call:
                # No tool call - we're done
                all_msgs.append(AIMessage(content=content))
                return {
                    "content": content,
                    "messages": all_msgs,
                    "tool_calls": tool_calls_count,
                    "tools_used": tools_used,
                }

            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"] or {}

            # Validate tool exists
            available_names = [t.name for t in self.mcp_tools]
            if tool_name not in available_names:
                # Unknown tool - feed error back and let LLM retry
                error_msg = f"工具 '{tool_name}' 不存在。可用工具：{', '.join(available_names)}"
                all_msgs.append(AIMessage(content=content))
                all_msgs.append(
                    ToolMessage(content=error_msg, tool_call_id=f"call_{iteration}")
                )
                tool_calls_count += 1
                continue

            # Execute the tool
            try:
                tool_result = self.call_mcp_tool_text(tool_name, tool_args)
            except Exception as e:
                tool_result = f"工具调用失败: {str(e)}"

            tools_used.append(tool_name)
            tool_calls_count += 1

            # Append AI response + tool result to messages
            all_msgs.append(AIMessage(content=content))
            all_msgs.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=f"call_{iteration}",
                    name=tool_name,
                )
            )

        # Max iterations reached - return last response (or error)
        last_msg = all_msgs[-1] if all_msgs else None
        final_content = (
            last_msg.content if isinstance(last_msg, AIMessage) else ""
        ) if last_msg else ""
        if not final_content:
            final_content = "已达到最大工具调用次数，未能完成任务。"

        return {
            "content": final_content,
            "messages": all_msgs,
            "tool_calls": tool_calls_count,
            "tools_used": tools_used,
        }

    # ── Core invoke methods (no DB recording) ────────────────────────────────

    def invoke(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke the agent synchronously.

        Args:
            input_data: Input data for the agent.
            config: Optional run configuration.

        Returns:
            Agent output as a dictionary.
        """
        return self.graph.invoke(input_data, config=config)

    async def ainvoke(
        self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke the agent asynchronously.

        Args:
            input_data: Input data for the agent.
            config: Optional run configuration.

        Returns:
            Agent output as a dictionary.
        """
        return await self.graph.ainvoke(input_data, config=config)

    def stream(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Stream the agent's output synchronously.

        Args:
            input_data: Input data for the agent.
            config: Optional run configuration.

        Yields:
            Output chunks from the agent.
        """
        yield from self.graph.stream(input_data, config=config)

    async def astream(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Stream the agent's output asynchronously.

        Args:
            input_data: Input data for the agent.
            config: Optional run configuration.

        Yields:
            Output chunks from the agent.
        """
        async for chunk in self.graph.astream(input_data, config=config):
            yield chunk

    # ── Invoke with run recording (DB-backed) ────────────────────────────────

    def _make_summary(self, data: Any, max_len: int = 500) -> Optional[str]:
        """Create a truncated summary string from arbitrary data.

        Filters out non-serializable objects (LLM instances, etc.) to avoid
        serialization errors when building run summaries.
        """
        if data is None:
            return None
        if isinstance(data, str):
            text = data
        elif isinstance(data, dict):
            # Filter out non-serializable values (e.g. LLM objects)
            clean = {}
            for k, v in data.items():
                try:
                    json.dumps({k: v}, ensure_ascii=False, default=str)
                    clean[k] = v
                except Exception:
                    clean[k] = f"<{type(v).__name__}>"
            try:
                text = json.dumps(clean, ensure_ascii=False, default=str)
            except Exception:
                text = str(clean)
        else:
            try:
                text = json.dumps(data, ensure_ascii=False, default=str)
            except Exception:
                text = str(data)
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    def invoke_with_run(
        self,
        input_data: Dict[str, Any],
        db: Session,
        agent_id: Optional[int] = None,
        project_id: Optional[int] = None,
        llm_config_id: Optional[int] = None,
        llm_model_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], int]:
        """Invoke the agent synchronously and record the run to the database.

        Args:
            input_data: Input data for the agent.
            db: Database session.
            agent_id: Agent metadata ID (optional).
            project_id: Project ID (optional).
            llm_config_id: LLM config ID used (optional).
            llm_model_name: LLM model name snapshot (optional).
            config: Optional LangGraph run configuration.

        Returns:
            Tuple of (output_dict, run_id).
        """
        from app.agents.callbacks import AgentRunCallbackHandler
        from app.schemas.agent import AgentRunCreate
        from app.services.agent_service import AgentService

        service = AgentService(db)

        # Create run record
        run = service.create_run(
            AgentRunCreate(
                agent_id=agent_id,
                project_id=project_id,
                status="pending",
                llm_config_id=llm_config_id,
                llm_model_name=llm_model_name,
                input_summary=self._make_summary(input_data),
            )
        )
        run_id = run.id

        # Create callback handler for step recording
        handler = AgentRunCallbackHandler(db, run_id)
        run_config = dict(config or {})
        callbacks = run_config.pop("callbacks", [])
        if isinstance(callbacks, list):
            callbacks = [*callbacks, handler]
        else:
            callbacks = [handler]
        run_config["callbacks"] = callbacks

        start_time = time.time()
        try:
            # Mark run as running
            service.start_run(run_id)

            result = self.graph.invoke(input_data, config=run_config)

            duration_ms = int((time.time() - start_time) * 1000)
            service.complete_run(
                run_id,
                output_summary=self._make_summary(result),
                duration_ms=duration_ms,
            )
            return result, run_id
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            try:
                service.fail_run(run_id, str(e))
            except Exception:
                pass
            raise

    async def ainvoke_with_run(
        self,
        input_data: Dict[str, Any],
        db: Session,
        agent_id: Optional[int] = None,
        project_id: Optional[int] = None,
        llm_config_id: Optional[int] = None,
        llm_model_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], int]:
        """Invoke the agent asynchronously and record the run to the database.

        Args:
            input_data: Input data for the agent.
            db: Database session.
            agent_id: Agent metadata ID (optional).
            project_id: Project ID (optional).
            llm_config_id: LLM config ID used (optional).
            llm_model_name: LLM model name snapshot (optional).
            config: Optional LangGraph run configuration.

        Returns:
            Tuple of (output_dict, run_id).
        """
        from app.agents.callbacks import AgentRunCallbackHandler
        from app.schemas.agent import AgentRunCreate
        from app.services.agent_service import AgentService

        service = AgentService(db)

        # Create run record
        run = service.create_run(
            AgentRunCreate(
                agent_id=agent_id,
                project_id=project_id,
                status="pending",
                llm_config_id=llm_config_id,
                llm_model_name=llm_model_name,
                input_summary=self._make_summary(input_data),
            )
        )
        run_id = run.id

        # Create callback handler for step recording
        handler = AgentRunCallbackHandler(db, run_id)
        run_config = dict(config or {})
        callbacks = run_config.pop("callbacks", [])
        if isinstance(callbacks, list):
            callbacks = [*callbacks, handler]
        else:
            callbacks = [handler]
        run_config["callbacks"] = callbacks

        start_time = time.time()
        try:
            # Mark run as running
            service.start_run(run_id)

            result = await self.graph.ainvoke(input_data, config=run_config)

            duration_ms = int((time.time() - start_time) * 1000)
            service.complete_run(
                run_id,
                output_summary=self._make_summary(result),
                duration_ms=duration_ms,
            )
            return result, run_id
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            try:
                service.fail_run(run_id, str(e))
            except Exception:
                pass
            raise
