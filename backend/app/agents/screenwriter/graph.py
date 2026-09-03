"""LangGraph state graph for the Screenwriter Agent.

The screenwriting pipeline has these stages:
1. analyze_idea  →  analyze the creative idea, generate logline + synopsis + characters
2. outline_scenes →  generate scene-by-scene outline
3. write_scene  →  write one scene in detail (loops for each scene)
4. review_script →  final quality review

State carries all accumulated writing data through the pipeline.
"""
import json
import re
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.agents.screenwriter.prompts import (
    IDEA_ANALYSIS_SYSTEM_PROMPT,
    IDEA_ANALYSIS_USER_TEMPLATE,
    SCENE_OUTLINE_SYSTEM_PROMPT,
    SCENE_OUTLINE_USER_TEMPLATE,
    SCENE_WRITING_SYSTEM_PROMPT,
    SCENE_WRITING_USER_TEMPLATE,
    SCRIPT_REVIEW_SYSTEM_PROMPT,
    SCRIPT_REVIEW_USER_TEMPLATE,
)


class ScreenwriterState(TypedDict):
    """State schema for the screenwriter agent.

    Attributes:
        idea: The original creative idea from the user.
        genre: Story genre.
        style: Writing style / tone.
        num_scenes: Target number of scenes.
        logline: One-sentence story premise.
        synopsis: Full story synopsis.
        characters: List of character info dicts.
        scene_outlines: List of scene outline dicts (skeleton only).
        current_scene_index: Index of the scene currently being written.
        scenes: List of fully-written scene dicts (with dialogues).
        review: Final review / quality assessment dict.
        current_stage: Current pipeline stage name (for tracking).
        error: Error message if any stage fails.
    """

    # Input
    idea: str
    genre: str
    style: str
    num_scenes: int

    # Analysis output
    logline: str
    synopsis: str
    characters: list[dict[str, Any]]

    # Outline
    scene_outlines: list[dict[str, Any]]

    # Writing
    current_scene_index: int
    scenes: list[dict[str, Any]]

    # Review
    review: dict[str, Any]

    # Meta
    current_stage: str
    error: str


def _extract_json(text: str) -> Any:
    """Try to extract a JSON object or array from LLM output text.

    Handles markdown code fences and stray text around the JSON.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # Try to find the first { ... } or [ ... ] block
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Failed to extract JSON from LLM output:\n{text[:500]}")


def _safe_str(value: Any) -> str:
    """Safely convert any value to string for prompt injection."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def create_screenwriter_graph(llm):
    """Create and compile the screenwriter agent state graph.

    Args:
        llm: The language model to use.

    Returns:
        Compiled LangGraph state graph.
    """

    # ── Node: analyze idea ────────────────────────────────────────────────

    def analyze_idea(state: ScreenwriterState) -> dict:
        """Analyze the creative idea and generate logline, synopsis, and characters."""
        logger.info(f"[Screenwriter] Stage: analyze_idea — idea='{state['idea'][:50]}...'")

        user_prompt = IDEA_ANALYSIS_USER_TEMPLATE.format(
            idea=state["idea"],
            genre=state["genre"],
            style=state["style"] or "默认风格",
            num_scenes=state["num_scenes"],
        )

        messages = [
            SystemMessage(content=IDEA_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = llm.invoke(messages)
            result = _extract_json(response.content)

            return {
                "logline": result.get("logline", ""),
                "synopsis": result.get("synopsis", ""),
                "characters": result.get("characters", []),
                "num_scenes": result.get("num_scenes", state["num_scenes"]),
                "genre": result.get("genre", state["genre"]),
                "style": result.get("style", state["style"]),
                "current_stage": "idea_analyzed",
            }
        except Exception as e:
            logger.error(f"[Screenwriter] analyze_idea failed: {e}")
            return {"error": f"创意分析失败: {str(e)}", "current_stage": "error"}

    # ── Node: outline scenes ─────────────────────────────────────────────

    def outline_scenes(state: ScreenwriterState) -> dict:
        """Generate the scene-by-scene outline."""
        logger.info(f"[Screenwriter] Stage: outline_scenes — target={state['num_scenes']} scenes")

        user_prompt = SCENE_OUTLINE_USER_TEMPLATE.format(
            logline=state.get("logline", ""),
            synopsis=state.get("synopsis", ""),
            characters_json=_safe_str(state.get("characters", [])),
            num_scenes=state["num_scenes"],
        )

        messages = [
            SystemMessage(content=SCENE_OUTLINE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = llm.invoke(messages)
            outlines = _extract_json(response.content)

            # Normalize to list
            if isinstance(outlines, dict) and "scenes" in outlines:
                outlines = outlines["scenes"]

            return {
                "scene_outlines": outlines,
                "current_scene_index": 0,
                "scenes": [],
                "current_stage": "outlined",
            }
        except Exception as e:
            logger.error(f"[Screenwriter] outline_scenes failed: {e}")
            return {"error": f"场景大纲生成失败: {str(e)}", "current_stage": "error"}

    # ── Node: write scene ────────────────────────────────────────────────

    def write_scene(state: ScreenwriterState) -> dict:
        """Write one scene in detail. Called in a loop for each scene."""
        idx = state.get("current_scene_index", 0)
        outlines = state.get("scene_outlines", [])
        total = len(outlines)

        if idx >= total:
            # All scenes written, move to review
            return {"current_stage": "all_scenes_written"}

        outline = outlines[idx]
        logger.info(f"[Screenwriter] Stage: write_scene — scene {idx + 1}/{total}")

        # Context: previous and next scene summaries
        prev_summary = outlines[idx - 1].get("description", "") if idx > 0 else "（开场，无前情）"
        next_summary = outlines[idx + 1].get("description", "") if idx < total - 1 else "（结尾，无后续）"

        key_chars = outline.get("key_characters", [])
        if isinstance(key_chars, list):
            key_chars_str = "、".join(key_chars)
        else:
            key_chars_str = str(key_chars)

        user_prompt = SCENE_WRITING_USER_TEMPLATE.format(
            logline=state.get("logline", ""),
            genre=state.get("genre", ""),
            style=state.get("style", ""),
            characters_json=_safe_str(state.get("characters", [])),
            scene_number=idx + 1,
            location=outline.get("location", "未知地点"),
            int_ext=outline.get("int_ext", "INT"),
            time_of_day=outline.get("time_of_day", "日"),
            scene_description=outline.get("description", ""),
            key_characters=key_chars_str,
            prev_scene_summary=prev_summary,
            next_scene_summary=next_summary,
        )

        messages = [
            SystemMessage(content=SCENE_WRITING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = llm.invoke(messages)
            scene_data = _extract_json(response.content)

            # Build the full scene object
            full_scene = {
                "scene_number": outline.get("scene_number", str(idx + 1)),
                "location": outline.get("location", ""),
                "int_ext": outline.get("int_ext", "INT"),
                "time_of_day": outline.get("time_of_day", "日"),
                "description": scene_data.get("description", outline.get("description", "")),
                "dialogues": scene_data.get("dialogues", []),
                "beat": outline.get("beat", ""),
                "key_characters": outline.get("key_characters", []),
                "order_index": idx,
            }

            updated_scenes = state.get("scenes", []) + [full_scene]

            return {
                "scenes": updated_scenes,
                "current_scene_index": idx + 1,
                "current_stage": f"writing_scene_{idx + 1}",
            }
        except Exception as e:
            logger.error(f"[Screenwriter] write_scene {idx + 1} failed: {e}")
            # Continue with a placeholder instead of failing the whole script
            placeholder_scene = {
                "scene_number": outline.get("scene_number", str(idx + 1)),
                "location": outline.get("location", ""),
                "int_ext": outline.get("int_ext", "INT"),
                "time_of_day": outline.get("time_of_day", "日"),
                "description": outline.get("description", ""),
                "dialogues": [],
                "beat": outline.get("beat", ""),
                "key_characters": outline.get("key_characters", []),
                "order_index": idx,
                "_note": f"生成失败: {str(e)}",
            }
            updated_scenes = state.get("scenes", []) + [placeholder_scene]
            return {
                "scenes": updated_scenes,
                "current_scene_index": idx + 1,
                "current_stage": f"writing_scene_{idx + 1}_partial",
            }

    # ── Node: review script ──────────────────────────────────────────────

    def review_script(state: ScreenwriterState) -> dict:
        """Final quality review of the complete script."""
        logger.info("[Screenwriter] Stage: review_script")

        scenes = state.get("scenes", [])
        scenes_summary = "\n".join(
            f"第{i+1}场 - {s.get('location', '')}（{s.get('beat', '')}）: {s.get('description', '')[:80]}"
            for i, s in enumerate(scenes)
        )

        user_prompt = SCRIPT_REVIEW_USER_TEMPLATE.format(
            logline=state.get("logline", ""),
            synopsis=state.get("synopsis", ""),
            scenes_summary=scenes_summary,
        )

        messages = [
            SystemMessage(content=SCRIPT_REVIEW_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = llm.invoke(messages)
            review = _extract_json(response.content)

            return {
                "review": review,
                "current_stage": "complete",
            }
        except Exception as e:
            logger.error(f"[Screenwriter] review_script failed: {e}")
            return {
                "review": {"overall_score": 0, "issues": [f"审校失败: {str(e)}"]},
                "current_stage": "complete_with_review_error",
            }

    # ── Conditional edges ────────────────────────────────────────────────

    def should_continue_writing(state: ScreenwriterState) -> str:
        """Decide whether to write the next scene or move to review."""
        idx = state.get("current_scene_index", 0)
        total = len(state.get("scene_outlines", []))
        if idx < total:
            return "write_next"
        return "review"

    def check_error(state: ScreenwriterState) -> str:
        """Check if an error occurred and route accordingly."""
        if state.get("error"):
            return "error"
        return "continue"

    # ── Build graph ──────────────────────────────────────────────────────

    graph = StateGraph(ScreenwriterState)

    graph.add_node("analyze_idea", analyze_idea)
    graph.add_node("outline_scenes", outline_scenes)
    graph.add_node("write_scene", write_scene)
    graph.add_node("review_script", review_script)

    # Main flow
    graph.add_edge(START, "analyze_idea")
    graph.add_edge("analyze_idea", "outline_scenes")
    graph.add_edge("outline_scenes", "write_scene")

    # Scene writing loop: write_scene → write_scene (next scene) or review
    graph.add_conditional_edges(
        "write_scene",
        should_continue_writing,
        {
            "write_next": "write_scene",
            "review": "review_script",
        },
    )

    graph.add_edge("review_script", END)

    return graph