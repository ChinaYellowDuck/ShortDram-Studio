"""Screenwriter Agent - generates and refines short drama scripts.

This agent orchestrates the full screenwriting pipeline:
1. Idea analysis → logline, synopsis, characters
2. Scene outline → scene-by-scene skeleton
3. Scene writing → detailed scenes with dialogue (looped)
4. Script review → quality assessment

It also supports incremental refinement of individual scenes or the whole script.
"""
import json
import re
from typing import Any, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from loguru import logger

from app.agents.base import BaseAgent
from app.agents.screenwriter.graph import _extract_json, create_screenwriter_graph
from app.agents.screenwriter.prompts import (
    SCENE_WRITING_SYSTEM_PROMPT,
    SCENE_WRITING_USER_TEMPLATE,
)


class ScreenwriterAgent(BaseAgent):
    """Screenwriter agent for generating and refining short drama scripts.

    Provides high-level methods for full script generation and targeted refinement.
    """

    def __init__(self, llm: BaseChatModel, config: Optional[Dict[str, Any]] = None):
        super().__init__(llm, config)

    @property
    def name(self) -> str:
        """Agent name."""
        return "screenwriter"

    @property
    def description(self) -> str:
        """Human-readable description."""
        return "编剧智能体 - 从创意生成完整短剧剧本，支持多轮打磨"

    def build_graph(self) -> StateGraph:
        """Build the screenwriter state graph.

        Returns:
            Compiled LangGraph state graph.
        """
        return create_screenwriter_graph(self.llm)

    # ── High-level methods ───────────────────────────────────────────────

    def generate_script(
        self,
        idea: str,
        genre: str = "都市",
        style: Optional[str] = None,
        num_scenes: int = 10,
    ) -> Dict[str, Any]:
        """Generate a complete script from a creative idea.

        Runs the full pipeline: idea analysis → scene outline → scene writing → review.

        Args:
            idea: Creative idea / concept description.
            genre: Story genre.
            style: Writing style / tone.
            num_scenes: Target number of scenes.

        Returns:
            Dict with the full script data including:
            - logline, synopsis, characters, scenes (with dialogues), review
        """
        logger.info(
            f"[Screenwriter] Generating script: genre={genre}, "
            f"num_scenes={num_scenes}, idea='{idea[:50]}...'"
        )

        initial_state = {
            "idea": idea,
            "genre": genre,
            "style": style or "",
            "num_scenes": num_scenes,
            "logline": "",
            "synopsis": "",
            "characters": [],
            "scene_outlines": [],
            "current_scene_index": 0,
            "scenes": [],
            "review": {},
            "current_stage": "starting",
            "error": "",
        }

        result = self.invoke(initial_state)
        return result

    async def agenerate_script(
        self,
        idea: str,
        genre: str = "都市",
        style: Optional[str] = None,
        num_scenes: int = 10,
    ) -> Dict[str, Any]:
        """Async version of generate_script."""
        logger.info(
            f"[Screenwriter] Async generating script: genre={genre}, "
            f"num_scenes={num_scenes}, idea='{idea[:50]}...'"
        )

        initial_state = {
            "idea": idea,
            "genre": genre,
            "style": style or "",
            "num_scenes": num_scenes,
            "logline": "",
            "synopsis": "",
            "characters": [],
            "scene_outlines": [],
            "current_scene_index": 0,
            "scenes": [],
            "review": {},
            "current_stage": "starting",
            "error": "",
        }

        result = await self.ainvoke(initial_state)
        return result

    def refine_scene(
        self,
        scene_data: Dict[str, Any],
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Refine a single scene based on user feedback.

        Args:
            scene_data: Current scene data (location, description, dialogues, etc.).
            feedback: User feedback / revision instructions.
            context: Optional context dict with logline, genre, characters, etc.

        Returns:
            Refined scene data dict.
        """
        context = context or {}

        logger.info(
            f"[Screenwriter] Refining scene: "
            f"scene='{scene_data.get('location', '')}', "
            f"feedback='{feedback[:50]}...'"
        )

        characters_json = json.dumps(
            context.get("characters", []), ensure_ascii=False, indent=2
        )

        user_prompt = SCENE_WRITING_USER_TEMPLATE.format(
            logline=context.get("logline", ""),
            genre=context.get("genre", ""),
            style=context.get("style", ""),
            characters_json=characters_json,
            scene_number=scene_data.get("scene_number", "?"),
            location=scene_data.get("location", ""),
            int_ext=scene_data.get("int_ext", "INT"),
            time_of_day=scene_data.get("time_of_day", "日"),
            scene_description=scene_data.get("description", ""),
            key_characters=", ".join(scene_data.get("key_characters", [])),
            prev_scene_summary=context.get("prev_scene_summary", "（无上下文）"),
            next_scene_summary=context.get("next_scene_summary", "（无上下文）"),
        )

        refine_instruction = (
            f"\n\n【修改要求】\n请根据以下反馈重写这个场景：\n{feedback}\n\n"
            f"【原场景内容】\n描述：{scene_data.get('description', '')}\n\n"
            f"原对白：\n"
        )
        for i, dlg in enumerate(scene_data.get("dialogues", [])):
            refine_instruction += (
                f"{i+1}. {dlg.get('character_name', '')}"
                f"（{dlg.get('emotion', '正常')}）: {dlg.get('dialogue', '')}\n"
            )
            if dlg.get("action"):
                refine_instruction += f"   动作: {dlg['action']}\n"

        refine_instruction += "\n请输出完整的重写后场景（JSON格式）。"

        messages = [
            SystemMessage(content=SCENE_WRITING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt + refine_instruction),
        ]

        try:
            response = self.llm.invoke(messages)
            refined = _extract_json(response.content)

            # Merge with original scene metadata
            result = {
                **scene_data,
                "description": refined.get("description", scene_data.get("description", "")),
                "dialogues": refined.get("dialogues", scene_data.get("dialogues", [])),
            }
            return result
        except Exception as e:
            logger.error(f"[Screenwriter] refine_scene failed: {e}")
            raise

    async def arefine_scene(
        self,
        scene_data: Dict[str, Any],
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Async version of refine_scene."""
        # For async, just use the sync version wrapped in a simpler call
        # since llm.invoke is typically async-capable via ainvoke
        context = context or {}

        logger.info(
            f"[Screenwriter] Async refining scene: "
            f"scene='{scene_data.get('location', '')}', "
            f"feedback='{feedback[:50]}...'"
        )

        characters_json = json.dumps(
            context.get("characters", []), ensure_ascii=False, indent=2
        )

        user_prompt = SCENE_WRITING_USER_TEMPLATE.format(
            logline=context.get("logline", ""),
            genre=context.get("genre", ""),
            style=context.get("style", ""),
            characters_json=characters_json,
            scene_number=scene_data.get("scene_number", "?"),
            location=scene_data.get("location", ""),
            int_ext=scene_data.get("int_ext", "INT"),
            time_of_day=scene_data.get("time_of_day", "日"),
            scene_description=scene_data.get("description", ""),
            key_characters=", ".join(scene_data.get("key_characters", [])),
            prev_scene_summary=context.get("prev_scene_summary", "（无上下文）"),
            next_scene_summary=context.get("next_scene_summary", "（无上下文）"),
        )

        refine_instruction = (
            f"\n\n【修改要求】\n请根据以下反馈重写这个场景：\n{feedback}\n\n"
            f"【原场景内容】\n描述：{scene_data.get('description', '')}\n\n"
            f"原对白：\n"
        )
        for i, dlg in enumerate(scene_data.get("dialogues", [])):
            refine_instruction += (
                f"{i+1}. {dlg.get('character_name', '')}"
                f"（{dlg.get('emotion', '正常')}）: {dlg.get('dialogue', '')}\n"
            )
            if dlg.get("action"):
                refine_instruction += f"   动作: {dlg['action']}\n"

        refine_instruction += "\n请输出完整的重写后场景（JSON格式）。"

        messages = [
            SystemMessage(content=SCENE_WRITING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt + refine_instruction),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            refined = _extract_json(response.content)

            result = {
                **scene_data,
                "description": refined.get("description", scene_data.get("description", "")),
                "dialogues": refined.get("dialogues", scene_data.get("dialogues", [])),
            }
            return result
        except Exception as e:
            logger.error(f"[Screenwriter] arefine_scene failed: {e}")
            raise