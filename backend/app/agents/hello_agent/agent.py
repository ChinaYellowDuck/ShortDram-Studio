"""Hello Agent - a simple example agent for testing.

This agent demonstrates the basic agent pattern:
- Inherits from BaseAgent
- Implements build_graph() using LangGraph
- Provides a simple chat interface
"""
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph

from app.agents.base import BaseAgent
from app.agents.hello_agent.graph import create_hello_graph


class HelloAgent(BaseAgent):
    """A simple hello/greeting agent for testing the agent framework.

    This agent takes a user message and returns a friendly greeting response.
    """

    def __init__(self, llm: BaseChatModel, config: Optional[Dict[str, Any]] = None):
        super().__init__(llm, config)

    @property
    def name(self) -> str:
        """Agent name."""
        return "hello_agent"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "A simple greeting agent for testing the agent framework"

    def build_graph(self) -> StateGraph:
        """Build the Hello Agent state graph.

        Returns:
            Compiled LangGraph state graph.
        """
        return create_hello_graph(self.llm)

    def chat(self, message: str) -> str:
        """Send a message to the agent and get a response.

        Args:
            message: User input message.

        Returns:
            Agent response text.
        """
        result = self.invoke({"messages": [HumanMessage(content=message)]})
        return result.get("greeting", "")

    async def achat(self, message: str) -> str:
        """Send a message to the agent asynchronously.

        Args:
            message: User input message.

        Returns:
            Agent response text.
        """
        result = await self.ainvoke({"messages": [HumanMessage(content=message)]})
        return result.get("greeting", "")
