"""Producer Agent - lightweight orchestrator for the short drama production pipeline.

In v0.1, the producer agent:
1. Validates the creative idea
2. Orchestrates the screenwriter agent to generate a full script
3. Returns the complete result

Future versions will add quality review loops, multi-agent coordination,
and human-in-the-loop review nodes.
"""
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langgraph.graph import StateGraph
from loguru import logger

from app.agents.base import BaseAgent
from app.agents.producer.graph import create_producer_graph


class ProducerAgent(BaseAgent):
    """Producer agent that orchestrates the full short drama production pipeline.

    Acts as the entry point for end-to-end script creation from a raw idea.
    """

    def __init__(self, llm: BaseChatModel, config: Optional[Dict[str, Any]] = None):
        super().__init__(llm, config)

    @property
    def name(self) -> str:
        """Agent name."""
        return "producer"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "制片人智能体 - 统筹短剧制作全流程，从创意到成品的协调者"

    def build_graph(self) -> StateGraph:
        """Build the producer state graph.

        Returns:
            Compiled LangGraph state graph.
        """
        return create_producer_graph()

    # ── High-level methods ───────────────────────────────────────────────

    def create_project_from_idea(
        self,
        idea: str,
        project_name: str = "",
        genre: str = "都市",
        style: Optional[str] = None,
        num_scenes: int = 10,
    ) -> Dict[str, Any]:
        """Create a complete project from a creative idea.

        Runs the full producer pipeline: validation → screenwriting.

        Args:
            idea: Creative idea / concept description.
            project_name: Optional project name (auto-generated if empty).
            genre: Story genre.
            style: Writing style / tone.
            num_scenes: Target number of scenes.

        Returns:
            Dict with project info, validation result, and full script data.
        """
        # Auto-generate project name if not provided
        if not project_name:
            # Use first 20 chars of idea as project name
            project_name = idea[:20].strip() + "..." if len(idea) > 20 else idea

        logger.info(
            f"[Producer] Creating project: name='{project_name}', "
            f"genre={genre}, num_scenes={num_scenes}"
        )

        initial_state = {
            "project_name": project_name,
            "idea": idea,
            "genre": genre,
            "style": style or "",
            "num_scenes": num_scenes,
            "llm": self.llm,
            "validation": {},
            "script_result": {},
            "current_stage": "starting",
            "error": "",
        }

        result = self.invoke(initial_state)

        return {
            "project_name": result.get("project_name", project_name),
            "validation": result.get("validation", {}),
            "script": result.get("script_result", {}),
            "current_stage": result.get("current_stage", ""),
            "error": result.get("error", ""),
        }

    async def acreate_project_from_idea(
        self,
        idea: str,
        project_name: str = "",
        genre: str = "都市",
        style: Optional[str] = None,
        num_scenes: int = 10,
    ) -> Dict[str, Any]:
        """Async version of create_project_from_idea."""
        if not project_name:
            project_name = idea[:20].strip() + "..." if len(idea) > 20 else idea

        logger.info(
            f"[Producer] Async creating project: name='{project_name}', "
            f"genre={genre}, num_scenes={num_scenes}"
        )

        initial_state = {
            "project_name": project_name,
            "idea": idea,
            "genre": genre,
            "style": style or "",
            "num_scenes": num_scenes,
            "llm": self.llm,
            "validation": {},
            "script_result": {},
            "current_stage": "starting",
            "error": "",
        }

        result = await self.ainvoke(initial_state)

        return {
            "project_name": result.get("project_name", project_name),
            "validation": result.get("validation", {}),
            "script": result.get("script_result", {}),
            "current_stage": result.get("current_stage", ""),
            "error": result.get("error", ""),
        }