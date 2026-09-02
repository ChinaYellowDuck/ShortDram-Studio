"""Base classes and interfaces for all agents."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph


class BaseAgent(ABC):
    """Abstract base class for all agents.

    All agents should inherit from this class and implement the required methods.
    """

    def __init__(self, llm: BaseChatModel, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent.

        Args:
            llm: The language model to use.
            config: Optional agent-specific configuration.
        """
        self.llm = llm
        self.config = config or {}
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
