"""Tests for agent tool calling (BaseAgent invoke_with_tools)."""
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agents.base import BaseAgent
from app.agents.mcp_client import McpTool


class DummyAgent(BaseAgent):
    """Concrete test implementation of BaseAgent."""

    @property
    def name(self):
        return "dummy"

    @property
    def description(self):
        return "Test agent"

    @property
    def category(self):
        return "test"

    def build_graph(self):
        return None


def make_dummy_agent(mcp_tools=None, mcp_clients=None, llm_responses=None):
    """Create a DummyAgent with a mocked LLM that returns given responses."""
    mock_llm = MagicMock()
    if llm_responses is not None:
        mock_llm.invoke.side_effect = [AIMessage(content=r) for r in llm_responses]
    else:
        mock_llm.invoke.return_value = AIMessage(content="hello")

    return DummyAgent(llm=mock_llm, mcp_tools=mcp_tools or [], mcp_clients=mcp_clients or {})


def test_no_tools_simple_call():
    """When no MCP tools are available, just do a simple LLM call."""
    agent = make_dummy_agent(llm_responses=["直接回答"])
    result = agent.invoke_with_tools(
        [HumanMessage(content="你好")],
        system_prompt="你是助手",
    )

    assert result["tool_calls"] == 0
    assert result["tools_used"] == []
    assert "直接回答" in result["content"]
    # System + human + ai = 3 messages
    assert len(result["messages"]) == 3


def test_parse_tool_call_xml():
    """Test parsing tool call from <tool_call> tags."""
    agent = make_dummy_agent()
    text = '''思考中...

<tool_call>
{
  "name": "search",
  "arguments": {
    "query": "短剧制作流程"
  }
}
</tool_call>

继续思考...'''

    parsed = agent.parse_tool_call(text)
    assert parsed is not None
    assert parsed["name"] == "search"
    assert parsed["arguments"]["query"] == "短剧制作流程"


def test_parse_tool_call_plain_json():
    """Test parsing tool call from plain JSON pattern."""
    agent = make_dummy_agent()
    text = '{"name": "get_weather", "arguments": {"city": "beijing"}}'

    parsed = agent.parse_tool_call(text)
    assert parsed is not None
    assert parsed["name"] == "get_weather"
    assert parsed["arguments"]["city"] == "beijing"


def test_parse_tool_call_no_match():
    """Test that normal text returns None."""
    agent = make_dummy_agent()
    parsed = agent.parse_tool_call("这是普通回答，没有工具调用")
    assert parsed is None


def test_build_tools_prompt_empty_when_no_tools():
    """Tools prompt section is empty when no MCP tools."""
    agent = make_dummy_agent()
    assert agent.build_tools_prompt_section() == ""
    assert agent.has_mcp_tools() is False


def test_build_tools_prompt_with_tools():
    """Tools prompt section includes tool descriptions."""
    tools = [
        McpTool(
            name="search_knowledge",
            description="搜索知识库",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
            mcp_server_id=1,
            mcp_server_name="test-mcp",
        )
    ]
    agent = make_dummy_agent(mcp_tools=tools)

    assert agent.has_mcp_tools() is True
    section = agent.build_tools_prompt_section()
    assert "可用工具" in section
    assert "search_knowledge" in section
    assert "搜索知识库" in section
    assert "query" in section
    assert "<tool_call>" in section


def test_tool_call_loop_executes_tool():
    """Test the full ReAct loop: LLM calls tool → tool executed → LLM responds."""
    tools = [
        McpTool(
            name="search",
            description="搜索信息",
            input_schema={"type": "object", "properties": {}},
            mcp_server_id=1,
            mcp_server_name="test-mcp",
        )
    ]

    mock_client = MagicMock()
    mock_client.call_tool.return_value = {
        "content": [{"type": "text", "text": "搜索结果：短剧制作需要剧本、分镜、视频合成三个阶段"}]
    }

    agent = make_dummy_agent(
        mcp_tools=tools,
        mcp_clients={1: mock_client},
        llm_responses=[
            # First response: decide to call tool
            '<tool_call>{"name": "search", "arguments": {"query": "短剧制作"}}</tool_call>',
            # Second response: final answer after seeing tool result
            "根据搜索结果，短剧制作分为三个阶段...",
        ],
    )

    result = agent.invoke_with_tools(
        [HumanMessage(content="短剧制作流程是什么？")],
        system_prompt="你是专家",
    )

    assert result["tool_calls"] == 1
    assert result["tools_used"] == ["search"]
    assert "三个阶段" in result["content"]
    # Tool was actually called
    mock_client.call_tool.assert_called_once_with("search", {"query": "短剧制作"})
    # Messages: system + human + ai(tool_call) + tool + ai(final) = 5
    assert len(result["messages"]) == 5


def test_tool_call_unknown_tool_retries():
    """Unknown tool name gets an error response and LLM can retry."""
    tools = [
        McpTool(
            name="search",
            description="搜索",
            input_schema={"type": "object", "properties": {}},
            mcp_server_id=1,
            mcp_server_name="test-mcp",
        )
    ]

    agent = make_dummy_agent(
        mcp_tools=tools,
        mcp_clients={1: MagicMock()},
        llm_responses=[
            # First: call wrong tool
            '<tool_call>{"name": "nonexistent", "arguments": {}}</tool_call>',
            # Second: correct tool call
            '<tool_call>{"name": "search", "arguments": {}}</tool_call>',
            # Third: final answer
            "完成",
        ],
    )
    # Patch the tool call method for the second call
    agent.call_mcp_tool_text = MagicMock(return_value="搜索成功")  # type: ignore

    result = agent.invoke_with_tools([HumanMessage(content="test")])

    assert result["tool_calls"] == 2  # 1 unknown + 1 actual
    assert result["tools_used"] == ["search"]  # only the successful one
    assert "完成" in result["content"]


def test_max_iterations_prevents_infinite_loop():
    """Max iterations prevents infinite tool call loops."""
    tools = [
        McpTool(
            name="loop_tool",
            description="looper",
            input_schema={"type": "object", "properties": {}},
            mcp_server_id=1,
            mcp_server_name="test-mcp",
        )
    ]

    agent = make_dummy_agent(
        mcp_tools=tools,
        mcp_clients={1: MagicMock()},
        # Keep calling tool forever
        llm_responses=['<tool_call>{"name": "loop_tool", "arguments": {}}</tool_call>'] * 20,
    )
    agent.call_mcp_tool_text = MagicMock(return_value="still going")  # type: ignore

    result = agent.invoke_with_tools([HumanMessage(content="test")], max_iterations=3)

    assert result["tool_calls"] == 3
    assert len(result["tools_used"]) == 3
