"""Agent Manager - centralized agent instantiation and dispatch.

Provides a simple interface for services to invoke agents by key,
handling LLM config resolution, project-level overrides, and
graceful fallback when agents/LLMs are unavailable.
"""
from typing import Any, Dict, Optional

from loguru import logger

from app.agents.assistant.agent import AssistantAgent
from app.agents.hello_agent.agent import HelloAgent
from app.agents.screenwriter.agent import ScreenwriterAgent
from app.models.agent import Agent
from app.models.project_agent import ProjectAgentConfig


# Registry of agent classes by key
AGENT_REGISTRY = {
    "hello": HelloAgent,
    "screenwriter": ScreenwriterAgent,
    "assistant": AssistantAgent,
    # Add more agents as they're implemented
}


class AgentManager:
    """Manages agent instantiation and invocation.

    Usage:
        mgr = AgentManager(db_session)
        result = mgr.invoke("screenwriter", "generate_script", idea="...")
    """

    def __init__(self, db):
        self.db = db
        self._instances: Dict[str, Any] = {}

    def get_agent_instance(self, agent_key: str, project_id: Optional[int] = None):
        """Get or create an agent instance for the given key.

        Resolves LLM config with optional project-level overrides.
        Returns None if the agent or LLM config is unavailable.
        """
        cache_key = f"{agent_key}:{project_id or 'default'}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        # Look up agent metadata
        agent_meta = (
            self.db.query(Agent).filter(Agent.agent_key == agent_key).first()
        )
        if not agent_meta:
            logger.warning(f"[AgentManager] Agent '{agent_key}' not found in registry")
            return None

        if not agent_meta.is_enabled:
            logger.warning(f"[AgentManager] Agent '{agent_key}' is disabled")
            return None

        # Get agent class
        agent_cls = AGENT_REGISTRY.get(agent_key)
        if not agent_cls:
            logger.warning(f"[AgentManager] Agent class for '{agent_key}' not implemented")
            return None

        # Resolve LLM config with project override
        try:
            from app.services.agent_service import AgentService
            from app.agents.llm import LLMFactory

            agent_service = AgentService(self.db)

            # Check for project-level LLM override
            llm_config_id = None
            temperature = agent_meta.temperature or 0.7

            if project_id:
                project_cfg = (
                    self.db.query(ProjectAgentConfig)
                    .filter(
                        ProjectAgentConfig.project_id == project_id,
                        ProjectAgentConfig.agent_id == agent_meta.id,
                    )
                    .first()
                )
                if project_cfg:
                    if project_cfg.llm_config_override_id:
                        llm_config_id = project_cfg.llm_config_override_id
                    if project_cfg.temperature is not None:
                        temperature = project_cfg.temperature

            llm_config = agent_service.resolve_llm_config(
                agent_meta, requested_config_id=llm_config_id
            )
            llm = LLMFactory.create_from_config(
                llm_config,
                api_key=llm_config.api_key or "",  # encrypted; service decrypts
                temperature=temperature,
            )
        except Exception as e:
            logger.warning(f"[AgentManager] Failed to resolve LLM for '{agent_key}': {e}")
            return None

        # Load MCP tools for this agent
        mcp_tools: list = []
        mcp_clients: dict = {}
        try:
            mcp_tools, mcp_clients = self._load_mcp_tools(agent_meta)
        except Exception as e:
            logger.warning(f"[AgentManager] Failed to load MCP tools for '{agent_key}': {e}")
            # Continue without MCP tools - not fatal

        try:
            instance = agent_cls(
                llm=llm,
                mcp_tools=mcp_tools,
                mcp_clients=mcp_clients,
            )
            self._instances[cache_key] = instance
            return instance
        except Exception as e:
            logger.error(f"[AgentManager] Failed to instantiate agent '{agent_key}': {e}")
            return None

    def _load_mcp_tools(self, agent_meta) -> tuple[list, dict]:
        """Load MCP tools and build clients for an agent.

        Returns:
            Tuple of (mcp_tools_list, mcp_clients_dict keyed by server id).
        """
        from app.agents.mcp_client import McpTool, McpToolClient

        mcp_tools: list[McpTool] = []
        mcp_clients: dict[int, McpToolClient] = {}

        if not hasattr(agent_meta, 'mcps') or not agent_meta.mcps:
            return mcp_tools, mcp_clients

        for mcp_server in agent_meta.mcps:
            if not getattr(mcp_server, 'is_enabled', True):
                continue

            # Build client for this server
            client = McpToolClient(
                url=mcp_server.url,
                transport=mcp_server.transport,
                config=mcp_server.config or {},
                secrets=mcp_server.secrets or {},
                server_id=mcp_server.id,
                server_name=mcp_server.name,
            )
            mcp_clients[mcp_server.id] = client

            # Use cached tools if available, otherwise fetch
            if getattr(mcp_server, 'tools', None):
                for t in mcp_server.tools:
                    tool = McpTool(
                        name=t.get('name', 'unknown'),
                        description=t.get('description', ''),
                        input_schema=t.get('inputSchema') or t.get('input_schema'),
                        mcp_server_id=mcp_server.id,
                        mcp_server_name=mcp_server.name,
                    )
                    mcp_tools.append(tool)
            else:
                # Fetch tools from the server
                try:
                    fetched = client.list_tools()
                    mcp_tools.extend(fetched)
                except Exception as e:
                    logger.warning(
                        f"[AgentManager] Failed to list tools from MCP server '{mcp_server.name}': {e}"
                    )

        return mcp_tools, mcp_clients

    def invoke(
        self,
        agent_key: str,
        method: str,
        project_id: Optional[int] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """Invoke an agent method.

        Returns the result dict, or None if the agent is unavailable.
        """
        agent = self.get_agent_instance(agent_key, project_id)
        if not agent:
            return None

        try:
            func = getattr(agent, method, None)
            if not func or not callable(func):
                logger.error(f"[AgentManager] Agent '{agent_key}' has no method '{method}'")
                return None
            return func(**kwargs)
        except Exception as e:
            logger.error(f"[AgentManager] Agent '{agent_key}.{method}' failed: {e}")
            return None
