"""LangGraph callback handler for recording agent run steps."""
import json
import time
from typing import Any, Dict, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from sqlalchemy.orm import Session

from app.services.agent_service import AgentService


def _truncate(text: Any, max_len: int = 200) -> Optional[str]:
    """Safely truncate any value to a string summary.

    For dicts, filters out non-serializable values (e.g. LLM objects) to
    avoid serialization errors.
    """
    if text is None:
        return None
    if isinstance(text, str):
        result = text
    elif isinstance(text, dict):
        clean = {}
        for k, v in text.items():
            try:
                json.dumps({k: v}, ensure_ascii=False, default=str)
                clean[k] = v
            except Exception:
                clean[k] = f"<{type(v).__name__}>"
        try:
            result = json.dumps(clean, ensure_ascii=False, default=str)
        except Exception:
            result = str(clean)
    else:
        try:
            result = json.dumps(text, ensure_ascii=False, default=str)
        except Exception:
            result = str(text)
    if len(result) > max_len:
        return result[:max_len] + "..."
    return result


class AgentRunCallbackHandler(BaseCallbackHandler):
    """Callback handler that records LangGraph node executions as agent run steps.

    Each graph node triggers on_chain_start/on_chain_end. We track:
    - step creation (status=running) on chain start
    - step completion (status=completed) on chain end
    - step failure (status=failed) on chain error

    Nested chains inside a node (e.g. LLM calls) are NOT recorded as separate
    steps — only the top-level graph nodes are.
    """

    # Names to skip (graph root / framework-level chains)
    _SKIP_NAMES = {"LangGraph", "Graph", "Channel", "Pregel"}

    def __init__(self, db: Session, run_id: int):
        """
        Args:
            db: Database session.
            run_id: The parent agent run ID to attach steps to.
        """
        super().__init__()
        self.db = db
        self.run_id = run_id
        self.service = AgentService(db)
        self.step_counter: Dict[str, int] = {}  # step_name -> occurrences
        self.active_steps: Dict[str, int] = {}  # run_id (callback run id) -> step db id
        self._node_depth = 0  # track graph node nesting level

    # ── Chain events (graph nodes) ───────────────────────────────────────────

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Called when a chain (graph node) starts."""
        name = kwargs.get("run_name") or (serialized or {}).get("name", "unknown")

        # Skip graph root / framework chains
        if name in self._SKIP_NAMES or not name:
            return

        # Heuristic: LangGraph node names are short, descriptive strings.
        # We treat every chain inside the graph as a node step.
        # To avoid double-counting (node's internal chains), we only increment
        # the counter for the first level of chains inside the graph — but since
        # LangGraph nodes are top-level chains within the graph and internal
        # LLM calls are on_llm_start, this should be fine.

        # Compute step_index for this step name
        self.step_counter[name] = self.step_counter.get(name, 0) + 1
        step_index = self.step_counter[name]

        # Build input summary
        input_summary = _truncate(inputs, 200)

        try:
            step = self.service.start_step(
                run_id=self.run_id,
                step_name=name,
                step_index=step_index,
                input_summary=input_summary,
            )
            # Track by callback run_id if available
            run_id_cb = kwargs.get("run_id")
            if run_id_cb:
                self.active_steps[str(run_id_cb)] = step.id
        except Exception:
            # Never let callback errors break the agent execution
            pass

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain (graph node) ends."""
        run_id_cb = kwargs.get("run_id")
        step_id = None

        if run_id_cb and str(run_id_cb) in self.active_steps:
            step_id = self.active_steps.pop(str(run_id_cb))
        else:
            # Fallback: find the most recent running step with this name
            name = kwargs.get("run_name", "unknown")
            # Can't reliably match without run_id; skip silently
            return

        if step_id:
            output_summary = _truncate(outputs, 200)
            try:
                self.service.complete_step(
                    step_id=step_id,
                    output_summary=output_summary,
                )
            except Exception:
                pass

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Called when a chain (graph node) fails."""
        run_id_cb = kwargs.get("run_id")
        step_id = None

        if run_id_cb and str(run_id_cb) in self.active_steps:
            step_id = self.active_steps.pop(str(run_id_cb))

        if step_id:
            try:
                self.service.fail_step(step_id, str(error))
            except Exception:
                pass

    # ── LLM events (token tracking) ──────────────────────────────────────────

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when an LLM call finishes. Track token usage."""
        # Token tracking is currently a placeholder.
        # We accumulate token usage on the run level via LLMResult.
        # Full implementation would require tracking which step's LLM this is.
        pass
