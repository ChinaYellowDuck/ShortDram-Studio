"""Assistant Agent - general-purpose text processing agent.

A versatile "jack-of-all-trades" agent that handles miscellaneous text tasks:
- Summarization
- Rewriting / style adjustment
- Brainstorming
- Classification / tagging
- Content extraction
- Translation

Usage:
    agent = AssistantAgent(llm)
    result = agent.summarize(text, max_length=200)
    result = agent.rewrite(text, style="formal")
    result = agent.brainstorm(topic, num_ideas=10)
"""
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from loguru import logger

from app.agents.base import BaseAgent


ASSISTANT_SYSTEM_PROMPT = """你是 ShortDram Studio 的 AI 助理，一个多才多艺的短剧制作助手。

你的职责是处理各种文本类任务，包括但不限于：
• 内容总结与提炼
• 文本改写与风格调整
• 头脑风暴与创意发散
• 内容分类与打标签
• 关键信息提取
• 翻译与本地化

请用简洁、专业的中文回答。直接给出结果，不要过度寒暄。"""


class AssistantAgent(BaseAgent):
    """General-purpose assistant agent for miscellaneous text tasks."""

    def __init__(self, llm: BaseChatModel, config: Optional[Dict[str, Any]] = None):
        super().__init__(llm, config)

    @property
    def name(self) -> str:
        return "assistant"

    @property
    def description(self) -> str:
        return "通用助理智能体，负责文本总结、改写、头脑风暴等杂活"

    @property
    def category(self) -> str:
        return "辅助工具"

    def build_graph(self) -> StateGraph:
        """Simple pass-through graph - this agent uses direct LLM calls."""
        workflow = StateGraph(dict)

        def process(state: Dict[str, Any]) -> Dict[str, Any]:
            task = state.get("task", "process")
            text = state.get("text", "")
            params = state.get("params", {})

            result = self._dispatch(task, text, params)
            return {"result": result}

        workflow.add_node("process", process)
        workflow.set_entry_point("process")
        workflow.set_finish_point("process")
        return workflow.compile()

    # ── Task dispatch ──────────────────────────────────────────────────────

    def _dispatch(self, task: str, text: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the appropriate method based on task name."""
        task_map = {
            "summarize": self.summarize,
            "rewrite": self.rewrite,
            "brainstorm": self.brainstorm,
            "classify": self.classify,
            "extract": self.extract,
            "translate": self.translate,
        }
        func = task_map.get(task)
        if func:
            return func(text, **params)
        return {"result": self._freeform(text, params.get("instruction", ""))}

    # ── Public task methods ────────────────────────────────────────────────

    def summarize(self, text: str, max_length: int = 200, **kwargs) -> Dict[str, Any]:
        """Summarize text to a given max length."""
        logger.info(f"[Assistant] Summarizing {len(text)} chars → {max_length} chars")
        prompt = f"""请将以下内容总结为不超过 {max_length} 字的摘要，保留核心信息：

{text}

请直接输出摘要内容，不要加前缀或解释。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"summary": response.content.strip(), "original_length": len(text)}

    def rewrite(
        self,
        text: str,
        style: str = "normal",
        target_length: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Rewrite text in a different style."""
        logger.info(f"[Assistant] Rewriting text in '{style}' style")
        length_hint = f"，长度控制在 {target_length} 字左右" if target_length else ""
        prompt = f"""请将以下文本改写成「{style}」风格{length_hint}：

{text}

请直接输出改写后的内容。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"rewritten": response.content.strip(), "original": text, "style": style}

    def brainstorm(self, topic: str, num_ideas: int = 10, **kwargs) -> Dict[str, Any]:
        """Brainstorm ideas on a given topic."""
        logger.info(f"[Assistant] Brainstorming {num_ideas} ideas on '{topic[:50]}'")
        prompt = f"""围绕主题「{topic}」进行头脑风暴，生成 {num_ideas} 个有创意的点子。

要求：
• 每个点子简洁明了（1-2 句话）
• 点子之间要有差异，避免重复
• 要有一定的想象力和可行性

请用编号列表输出。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        # Parse numbered list into array
        raw = response.content.strip()
        ideas = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove number prefix like "1. " or "1、"
            import re
            cleaned = re.sub(r"^\d+[\.\、\)]\s*", "", line)
            if cleaned:
                ideas.append(cleaned)
        return {"topic": topic, "ideas": ideas[:num_ideas], "raw": raw}

    def classify(self, text: str, categories: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Classify text into categories."""
        logger.info(f"[Assistant] Classifying text")
        cat_text = "、".join(categories) if categories else "你认为合适的"
        prompt = f"""请对以下文本进行分类，从「{cat_text}」中选择最合适的1-3个标签：

{text}

请用 JSON 格式输出：{{"categories": ["标签1", "标签2"]}}"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        import json as _json
        try:
            parsed = _json.loads(response.content)
            return {"text": text[:100], "categories": parsed.get("categories", [])}
        except Exception:
            return {"text": text[:100], "categories": [], "raw": response.content.strip()}

    def extract(self, text: str, field: str = "key_points", **kwargs) -> Dict[str, Any]:
        """Extract specific information from text."""
        logger.info(f"[Assistant] Extracting '{field}' from text")
        prompt = f"""请从以下文本中提取「{field}」：

{text}

请用清晰的列表形式输出提取结果。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"field": field, "extracted": response.content.strip(), "source_length": len(text)}

    def translate(self, text: str, target_lang: str = "中文", **kwargs) -> Dict[str, Any]:
        """Translate text to target language."""
        logger.info(f"[Assistant] Translating {len(text)} chars to {target_lang}")
        prompt = f"""请将以下文本翻译成{target_lang}：

{text}

请直接输出翻译结果。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return {"translated": response.content.strip(), "original": text, "target_lang": target_lang}

    def _freeform(self, text: str, instruction: str) -> str:
        """Handle freeform tasks."""
        prompt = f"""任务：{instruction}

内容：
{text}

请执行上述任务。"""
        response = self.llm.invoke([
            SystemMessage(content=ASSISTANT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        return response.content.strip()
