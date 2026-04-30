"""ToM-specific output validators.

Called via the `after_step` hook. Validators inspect step output for
ToM-specific consistency violations (e.g., "second-order belief must
reference a first-order belief"). If a violation is found, a warning is
attached to the trace; the hook system does not fail-hard — downstream
recovery decisions are left to on_step_failure handlers.

This file is intentionally small — it is a demonstration of the pluggable
validator pattern, not an exhaustive ruleset.
"""

from __future__ import annotations

import logging
import re

from ...schemas import ExecutionContext, ExecutionTrace, Step

logger = logging.getLogger(__name__)

_BELIEF_REF = re.compile(r"(believes?|thinks?|以为)", re.IGNORECASE)


def after_step(step: Step, trace: ExecutionTrace, context: ExecutionContext) -> None:
    """Attach ToM consistency warnings to the trace (non-fatal)."""
    if not context.global_context:
        return
    desc = (step.description or "").lower()

    # Rule 1: second-order belief steps should cite first-order state
    if "second" in desc or "2nd" in desc or "���阶" in desc:
        accumulated = context.global_context.accumulated_results
        has_first_order = any(
            isinstance(v, (str, dict)) and _belief_mentioned(v)
            for phase_dict in accumulated.values()
            for v in (phase_dict.values() if isinstance(phase_dict, dict) else [phase_dict])
        )
        if not has_first_order:
            logger.info(
                f"[ToM validator] step {step.step_id[:8]}: second-order step ran "
                f"before any first-order belief was recorded — plan may be malformed"
            )

    # Rule 2: knowledge-gate steps should cite a prior knowledge-tracking step
    if "knowledge gate" in desc or "知识门" in desc:
        accumulated = context.global_context.accumulated_results
        has_knowledge_map = any(
            "knows" in str(v).lower() or "knowledge" in k.lower()
            for phase_dict in accumulated.values()
            for k, v in (phase_dict.items() if isinstance(phase_dict, dict) else [])
        )
        if not has_knowledge_map:
            logger.info(
                f"[ToM validator] step {step.step_id[:8]}: knowledge-gate without "
                f"prior knowledge-map entry in accumulated results"
            )


def _belief_mentioned(value) -> bool:
    s = str(value)
    return bool(_BELIEF_REF.search(s))
