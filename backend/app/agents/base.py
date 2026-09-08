"""Base classes and interfaces for all agents."""
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph
from sqlalchemy.orm import Session


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
