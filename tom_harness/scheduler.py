"""Scheduler — top-level orchestrator.

The Scheduler owns the end-to-end lifecycle:

    begin_task  →  plan  →  for each phase/step: execute  →  finalize  →  persist

It also owns:
  - Replan on step failure (bounded retries + optional plugin-driven recovery)
  - Writing successful (task, plan) pairs back into MemoryStore
  - Emitting the FinalResult envelope

The Scheduler itself is domain-agnostic. All ToM logic lives in plugins
registered against HookRegistry.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .context import ContextManager
from .executor import Executor
from .hooks import HookRegistry, RecoveryDirective
from .planner import Planner
from .registry import ToolRegistry
from .schemas import (
    ExecutionContext, ExecutionTrace, FinalResult, Memory, Plan,
    Step, TaskDescriptor,
)
from .tools.memory import MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    max_replans: int = 2
    persist_memories_on_success: bool = True
    halt_on_persistent_failure: bool = False  # if True, abort after retries exhausted


@dataclass
class Scheduler:
    planner: Planner
    executor: Executor
    registry: ToolRegistry
    context: ContextManager
    hooks: HookRegistry
    memory: MemoryStore
    config: SchedulerConfig = field(default_factory=SchedulerConfig)

    def run(
        self,
        *,
        task_id: str,
        question: str,
        options: dict[str, str] | None = None,
        dataset: str = "",
    ) -> FinalResult:
        t_start = time.time()
        self.context.begin_task(question=question, options=options)

        # 1. Plan
        try:
            plan = self.planner.plan(task_id=task_id, question=question, options=options)
        except Exception as e:  # noqa: BLE001
            logger.exception("Planning phase failed")
            return FinalResult(
                task_id=task_id, answer="", success=False,
                plan=_empty_plan(task_id), traces=[],
                elapsed_sec=time.time() - t_start,
                error=f"planning failed: {e}",
            )

        traces: list[ExecutionTrace] = []
        replans = 0
        exec_order = 0

        # 2. Execute — phase-by-phase, step-by-step
        completed_step_ids: set[str] = set()
        while True:
            failed = False
            for phase in plan.phases:
                for step in phase.steps:
                    exec_order += 1
                    # B6 fix: enforce depends_on. If any declared dependency
                    # has not yet completed, log a warning. We don't block
                    # execution (LLM-emitted depends_on is noisy), but the
                    # warning surfaces silent corruption to the runner log.
                    missing = [d for d in (step.depends_on or [])
                               if d and d not in completed_step_ids]
                    if missing:
                        logger.warning(
                            f"step {step.step_id[:8]} declares depends_on={step.depends_on} "
                            f"but {missing} are not yet completed — executing anyway"
                        )
                    ctx = ExecutionContext(
                        plan=plan,
                        current_phase_id=phase.phase_id,
                        current_step=step,
                        global_context=self.context.global_context,
                    )
                    trace = self.executor.execute_step(ctx, exec_order)
                    if trace.step_result.status == "completed":
                        completed_step_ids.add(step.step_id)
                    traces.append(trace)
                    if trace.step_result.status == "failed":
                        directive = self._gather_recovery_directive(step, trace, ctx)
                        if directive and directive.action == "replan" and replans < self.config.max_replans:
                            replans += 1
                            logger.info(f"Replanning (attempt {replans}) due to {directive.failure_type}")
                            plan = self._replan(
                                question=question,
                                options=options,
                                task_id=task_id,
                                failed_step=step,
                                directive=directive,
                            )
                            failed = True
                            break  # break phase loop, restart plan
                        elif directive and directive.action == "skip":
                            continue
                        elif directive and directive.action == "abort":
                            return self._finalize_failure(task_id, plan, traces, t_start,
                                                          error=f"abort directive: {directive.note}")
                        elif self.config.halt_on_persistent_failure:
                            return self._finalize_failure(task_id, plan, traces, t_start,
                                                          error="halted on persistent failure")
                if failed:
                    break
            if not failed:
                break  # all phases completed without triggering replan

        # 3. Finalize
        accumulated = self.context.global_context.accumulated_results if self.context.global_context else {}
        answer = self.executor.finalize_answer(question, options or {}, accumulated)
        success = bool(answer)

        # 4. Persist memory (enriched by plugins)
        if success and self.config.persist_memories_on_success:
            memory = Memory(
                task=TaskDescriptor(task_id=task_id, question=question, task_type=plan.task_type, dataset=dataset),
                plan=plan,
                execution_summary=_summarize_traces(traces),
                success=True,
                score=1.0,
            )
            enriched = self.hooks.fire("enrich_memory", memory=memory)
            for em in enriched:
                if isinstance(em, Memory):
                    memory = em
            self.memory.insert(memory)

        return FinalResult(
            task_id=task_id,
            answer=answer,
            success=success,
            plan=plan,
            traces=traces,
            elapsed_sec=time.time() - t_start,
            error=None if success else "finalize produced no answer",
            metadata={"replans": replans, "num_steps": exec_order},
        )

    # ── helpers ────────────────────────────────────────────────────────────
    def _gather_recovery_directive(
        self,
        step: Step,
        trace: ExecutionTrace,
        ctx: ExecutionContext,
    ) -> RecoveryDirective | None:
        """Let plugins propose a recovery; default is replan up to max."""
        proposals = self.hooks.fire("on_step_failure", step=step, trace=trace, context=ctx)
        for p in proposals:
            if isinstance(p, RecoveryDirective):
                return p
        # Default: replan once
        return RecoveryDirective(action="replan", failure_type="default", note="no plugin recovery")

    def _replan(
        self,
        *,
        question: str,
        options: dict[str, str] | None,
        task_id: str,
        failed_step: Step,
        directive: RecoveryDirective,
    ) -> Plan:
        # Tag the new plan with the failure note so the planner sees it
        self.context.record_step_result(
            "_last_failure",
            {"step_id": failed_step.step_id, "failure_type": directive.failure_type, "note": directive.note},
        )
        new_plan = self.planner.plan(task_id=task_id, question=question, options=options)
        return new_plan

    def _finalize_failure(
        self, task_id: str, plan: Plan, traces: list[ExecutionTrace], t_start: float, error: str,
    ) -> FinalResult:
        return FinalResult(
            task_id=task_id, answer="", success=False, plan=plan, traces=traces,
            elapsed_sec=time.time() - t_start, error=error,
        )


def _empty_plan(task_id: str) -> Plan:
    from .schemas import ExpectedFinalOutput
    return Plan(
        task_id=task_id, task_type="unknown", phases=[],
        expected_final_output=ExpectedFinalOutput(format="letter", description="single letter"),
    )


def _summarize_traces(traces: list[ExecutionTrace]) -> str:
    bits = []
    for t in traces:
        bits.append(f"[{t.execution_order}] {t.step_result.status}: {t.reasoning.thought[:80]}")
    return " | ".join(bits)
