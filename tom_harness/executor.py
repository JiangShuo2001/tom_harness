"""Executor Agent — ReAct loop per step.

The Executor consumes an ExecutionContext (one per step) and carries out:

    Reasoning  →  Acting  →  Observation  →  StepResult

For steps that declare `tool == None`, Acting is skipped and the LLM's
reasoning is treated as the output directly. This lets the same executor
handle both tool-using and pure-reasoning steps.

For steps with sub_steps, execution recurses depth-first. Each level
produces its own ExecutionTrace entries.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from .context import ContextManager
from .hooks import HookRegistry
from .llm import LLMClient
from .registry import ToolRegistry
from .schemas import (
    ExecutionContext, ExecutionTrace, Observation, Reasoning, Step, StepResult,
    ToolCall, ToolCallTrace, ToolType,
)
from .tools.skills import SkillLib

logger = logging.getLogger(__name__)


REASON_SYSTEM = """You are the Executor of a Theory-of-Mind reasoning agent. \
You are given one step from a reasoning plan, along with any Strategy Guide \
and Retrieved Knowledge in the context. Produce a brief JSON object:
{
  "thought": "<your analytical conclusion for this step>",
  "state_analysis": "<what prior context and step results matter>",
  "action_rationale": "<how you applied the strategy or reasoning to reach this conclusion>"
}
Output ONLY that JSON object."""

# ── Original REASON_SYSTEM (tool-aware) ──────────────────────────────────────
# REASON_SYSTEM = """You are the Executor of a Theory-of-Mind agent harness. \
# You are given one step from a plan. Produce a brief JSON object:
# {
#   "thought": "<one-sentence analysis>",
#   "state_analysis": "<what prior context matters for this step>",
#   "action_rationale": "<why the chosen tool/params will help, or why none>"
# }
# Output ONLY that JSON object."""


FINALIZE_SYSTEM = """You are the Finalizer. Given the question, options, \
and all accumulated step results, pick the single best answer letter.

CRITICAL: The Accumulated Step Results section contains the upstream \
reasoning, tool outputs, and any skill recommendations from earlier \
steps. You MUST base your answer on those results unless the story \
explicitly contradicts them. If any accumulated entry contains an \
'answer_letter' or 'recommendation' field with a valid letter, prefer \
it.

Reply with ONLY a JSON object: {"answer": "A" | "B" | "C" | "D"}"""


@dataclass
class Executor:
    """ReAct loop executor."""

    llm: LLMClient
    registry: ToolRegistry
    context: ContextManager
    hooks: HookRegistry
    skill_lib: SkillLib | None = None
    max_substep_depth: int = 3

    # ── public API ─────────────────────────────────────────────────────────
    def execute_step(self, ctx: ExecutionContext, execution_order: int) -> ExecutionTrace:
        step = ctx.current_step
        logger.info("[Executor] ── Step %d start ── %s", execution_order, step.description[:100])
        self.hooks.fire("before_step", step=ctx.current_step, context=ctx)
        trace = self._execute_one(ctx, execution_order, depth=0)
        self.hooks.fire("after_step", step=ctx.current_step, trace=trace, context=ctx)
        self.context.clear_transient()
        logger.info("[Executor] ── Step %d done ── status=%s", execution_order, trace.step_result.status)
        return trace


def _render_accumulated(accumulated, max_per_value=1500):
    """JSON-aware renderer. Replaces repr(v)[:400] which destroyed structured outputs."""
    import json as _json
    parts = []
    for k, v in accumulated.items():
        if isinstance(v, (dict, list)):
            try: rendered = _json.dumps(v, ensure_ascii=False, default=str)
            except Exception: rendered = repr(v)
        else:
            rendered = str(v)
        if len(rendered) > max_per_value:
            rendered = rendered[:max_per_value] + " [...truncated]"
        parts.append(f"- {k}: {rendered}")
    return "
".join(parts) if parts else "(empty — no upstream results)"


    def finalize_answer(self, question: str, options: dict[str, str], accumulated: dict[str, Any]) -> str:
        logger.info("[Executor] ── Finalize ── synthesizing answer from %d accumulated results", len(accumulated))
        self.hooks.fire("before_finalize", accumulated_results=accumulated)
        user = (
            f"## Question\n{question}\n\n"
            f"## Options\n" + "\n".join(f"{k}. {v}" for k, v in options.items() if v) + "\n\n"
            f"## Accumulated Step Results\n"
            + _render_accumulated(accumulated)
        )
        try:
            out = self.llm.chat_json(FINALIZE_SYSTEM, user, max_tokens=1024)
            ans = str(out.get("answer", "")).strip().upper()
            if ans in {"A", "B", "C", "D"}:
                logger.info("[Executor] ── Finalize ── answer=%s", ans)
                return ans
            logger.warning("[Executor] Finalize returned invalid answer: %s", out)
        except Exception as e:  # noqa: BLE001
            logger.warning("[Executor] Finalize JSON parse failed: %s", e)
        return ""

    # ── internals ──────────────────────────────────────────────────────────
    def _execute_one(
        self,
        ctx: ExecutionContext,
        execution_order: int,
        depth: int,
    ) -> ExecutionTrace:
        step = ctx.current_step
        t_step_start = time.time()

        # 1) Reason — ask LLM to produce a reasoning trio
        reasoning = self._reason_about(ctx)
        logger.info("[Executor]   Reasoning: %s", reasoning.thought[:150])

        # 2) Act — dispatch the step's tool if any
        tool_call_trace: ToolCallTrace | None = None
        observation: Observation | None = None
        if step.tool is not None and step.tool.tool_type != ToolType.NONE:
            logger.info("[Executor]   Acting: tool=%s:%s", step.tool.tool_type.value, step.tool.tool_name)
            tool_call_trace, observation = self._act(step.tool)
            if observation.success:
                logger.info("[Executor]   Observation: success, output=%s",
                             repr(observation.structured_output or observation.raw_output)[:200])
            else:
                logger.warning("[Executor]   Observation: FAILED — %s", observation.error)
        else:
            logger.info("[Executor]   Acting: pure reasoning (no tool)")

        # 3) Observe & store
        if observation is not None and observation.success and step.tool is not None:
            store_to = (
                step.tool.output_mapping.store_to
                if step.tool.output_mapping
                else f"{step.step_id[:8]}_result"
            )
            self.context.record_step_result(store_to, observation.structured_output or observation.raw_output)
        elif observation is None:
            # Pure reasoning step — store the reasoning conclusion so
            # subsequent steps and the Finalizer can see it.
            store_key = f"step_{execution_order}_reasoning"
            self.context.record_step_result(store_key, reasoning.thought)

        # 4) Recurse into sub_steps
        if step.sub_steps and depth < self.max_substep_depth:
            for sub in step.sub_steps:
                sub_ctx = ctx.model_copy(update={"current_step": sub})
                self._execute_one(sub_ctx, execution_order, depth + 1)

        status = "failed" if (observation is not None and not observation.success) else "completed"
        summary = (
            observation.error if (observation and not observation.success)
            else reasoning.thought
        )

        trace = ExecutionTrace(
            plan_id=ctx.plan.plan_id,
            step_id=step.step_id,
            phase_id=ctx.current_phase_id,
            execution_order=execution_order,
            reasoning=reasoning,
            tool_call=tool_call_trace,
            observation=observation,
            step_result=StepResult(status=status, output_summary=summary or ""),
        )
        logger.debug(
            f"step {step.step_id[:8]} status={status} "
            f"elapsed={time.time() - t_step_start:.2f}s"
        )
        return trace

    def _reason_about(self, ctx: ExecutionContext) -> Reasoning:
        step = ctx.current_step

        # Render the full plan overview so the executor sees the big picture
        plan_overview = self._render_plan_overview(ctx)

        user = (
            f"## Plan Overview\n{plan_overview}\n\n"
            f"## Task Context\n{self.context.render_dynamic_state(include_accumulated=True)}\n\n"
            f"## Current Step\n"
            f"description: {step.description}\n"
            f"expected_output: {step.expected_output_schema or '(unspecified)'}\n"
        )
        try:
            out = self.llm.chat_json(REASON_SYSTEM, user, max_tokens=512)
            return Reasoning(
                thought=str(out.get("thought", ""))[:500],
                state_analysis=str(out.get("state_analysis", ""))[:500],
                action_rationale=str(out.get("action_rationale", ""))[:500],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Reasoning JSON parse failed: {e}")
            return Reasoning(thought="(reasoning failed to parse)", state_analysis="", action_rationale="")

    @staticmethod
    def _render_plan_overview(ctx: ExecutionContext) -> str:
        """Render a compact plan overview marking the current step with >>>."""
        lines = [f"task_type: {ctx.plan.task_type}"]
        for phase in ctx.plan.phases:
            lines.append(f"Phase {phase.phase_order}: {phase.phase_name}")
            for step in phase.steps:
                marker = ">>>" if step.step_id == ctx.current_step.step_id else "   "
                lines.append(f"  {marker} Step {step.step_order}: {step.description[:120]}")
        return "\n".join(lines)

    def _act(self, call: ToolCall) -> tuple[ToolCallTrace, Observation]:
        # Inject an llm callback for declarative skills
        effective_params = dict(call.tool_params)
        if call.tool_type == ToolType.SKILL and "llm_fn" not in effective_params:
            effective_params["llm_fn"] = self.llm.chat
        effective_call = call.model_copy(update={"tool_params": effective_params})

        t0 = time.time()
        result = self.registry.dispatch(effective_call)
        duration_ms = int((time.time() - t0) * 1000)

        # Don't let `llm_fn` leak into the persisted trace
        trace_params = {k: v for k, v in call.tool_params.items() if k != "llm_fn"}
        trace = ToolCallTrace(
            tool_type=call.tool_type.value,
            tool_name=call.tool_name,
            params=trace_params,
            duration_ms=duration_ms,
        )
        observation = Observation(
            raw_output=result.raw_output,
            structured_output=result.structured_output or {},
            success=result.success,
            error=result.error,
        )
        return trace, observation
