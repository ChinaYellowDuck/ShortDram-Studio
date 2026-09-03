"""LangGraph state graph for the Producer Agent.

The producer agent is a lightweight orchestrator that:
1. Validates the creative idea (feasibility check)
2. Calls the screenwriter agent to generate a full script
3. Returns the complete project result

In v0.1, the producer acts as a simple pipeline coordinator.
In later versions, it will handle quality review loops and multi-agent coordination.
"""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.agents.screenwriter.agent import ScreenwriterAgent


class ProducerState(TypedDict):
    """State schema for the producer agent.

    Attributes:
        project_name: Name of the project being created.
        idea: Creative idea / concept.
        genre: Story genre.
        style: Writing style.
        num_scenes: Target number of scenes.
        llm: The LLM instance to pass to sub-agents.
        validation: Idea validation result dict.
        script_result: Complete script result from the screenwriter.
        current_stage: Current pipeline stage name.
        error: Error message if any stage fails.
    """

    # Input
    project_name: str
    idea: str
    genre: str
    style: str
    num_scenes: int
    llm: Any  # LLM instance (not serializable, passed at runtime)

    # Pipeline state
    validation: dict[str, Any]
    script_result: dict[str, Any]

    # Meta
    current_stage: str
    error: str


def create_producer_graph():
    """Create and compile the producer agent state graph.

    Returns:
        Compiled LangGraph state graph.
    """

    # ── Node: validate idea ──────────────────────────────────────────────

    def validate_idea(state: ProducerState) -> dict:
        """Validate the creative idea for feasibility and quality.

        In v0.1 this is a lightweight check — verifies the idea has enough
        substance to generate a script from. In later versions this will
        be a proper LLM-based feasibility assessment.
        """
        logger.info(f"[Producer] Stage: validate_idea — idea='{state['idea'][:50]}...'")

        idea = state["idea"].strip()
        issues = []
        score = 5

        # Basic length check
        if len(idea) < 10:
            issues.append("创意描述太短，可能无法生成完整剧本")
            score = 2
        elif len(idea) < 30:
            issues.append("创意描述较简略，生成结果可能不够丰富")
            score = 4
        else:
            score = 7

        # Genre check
        if not state.get("genre"):
            issues.append("未指定题材，将使用默认都市题材")

        is_feasible = score >= 3

        validation = {
            "is_feasible": is_feasible,
            "score": score,
            "issues": issues,
            "suggestions": [
                "如果生成结果不理想，可以尝试更详细地描述角色和核心冲突",
                "可以在生成后使用单场景打磨功能进行精细化调整",
            ] if is_feasible else ["请补充更详细的创意描述，包括主角、冲突、背景等"],
        }

        return {
            "validation": validation,
            "current_stage": "validated",
        }

    # ── Node: call screenwriter ─────────────────────────────────────────

    def call_screenwriter(state: ProducerState) -> dict:
        """Invoke the screenwriter agent to generate the full script."""
        logger.info("[Producer] Stage: call_screenwriter")

        try:
            screenwriter = ScreenwriterAgent(state["llm"])

            result = screenwriter.generate_script(
                idea=state["idea"],
                genre=state["genre"],
                style=state.get("style", ""),
                num_scenes=state["num_scenes"],
            )

            return {
                "script_result": result,
                "current_stage": "script_generated",
            }
        except Exception as e:
            logger.error(f"[Producer] call_screenwriter failed: {e}")
            return {
                "error": f"剧本生成失败: {str(e)}",
                "script_result": {},
                "current_stage": "error",
            }

    # ── Conditional edge ────────────────────────────────────────────────

    def should_proceed(state: ProducerState) -> str:
        """Decide whether to proceed with script generation based on validation."""
        if state.get("error"):
            return "end"

        validation = state.get("validation", {})
        if validation.get("is_feasible", False):
            return "generate"
        return "end"

    # ── Build graph ──────────────────────────────────────────────────────

    graph = StateGraph(ProducerState)

    graph.add_node("validate_idea", validate_idea)
    graph.add_node("call_screenwriter", call_screenwriter)

    graph.add_edge(START, "validate_idea")

    graph.add_conditional_edges(
        "validate_idea",
        should_proceed,
        {
            "generate": "call_screenwriter",
            "end": END,
        },
    )

    graph.add_edge("call_screenwriter", END)

    return graph