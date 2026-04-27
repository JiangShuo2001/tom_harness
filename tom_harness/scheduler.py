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
from .skill_router import SkillRouter
from .tools.memory import MemoryStore
from .tools.rag import RAGEngine

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
    skill_router: SkillRouter | None = None
    rag_engine: RAGEngine | None = None

    def run(
        self,
        *,
        task_id: str,
        question: str,
        options: dict[str, str] | None = None,
        dataset: str = "",
    ) -> FinalResult:
        t_start = time.time()
        logger.info("=" * 60)
        logger.info("[Scheduler] ══ Task start ══ id=%s", task_id)
        logger.info("[Scheduler] Question: %s", question[:200])
        self.planner.llm.reset_cache()
        self.context.begin_task(question=question, options=options)

        # 0.5  Hardcoded skill / RAG injection (Plan A experiment)
        if self.skill_router is not None:
            skill_id = self.skill_router.route(question, options or {})
            if skill_id:
                prompt = self.skill_router.get_skill_prompt(skill_id)
                if prompt:
                    self.context.install_skill(prompt)
                    logger.info("[Scheduler] Skill injected: %s", skill_id)

        if self.rag_engine is not None:
            try:
                rag_result = self.rag_engine.run(query=question, top_k=3)
                passages = rag_result.get("passages", [])
                if passages:
                    formatted = self.rag_engine.format_context(passages, max_length=1500)
                    if formatted:
                        self.context.install_rag_context(formatted)
                        logger.info("[Scheduler] RAG injected: %d passages", len(passages))
            except Exception as e:  # noqa: BLE001
                logger.warning("[Scheduler] RAG retrieval failed: %s", e)

        # 1. Plan
        try:
            plan = self.planner.plan(task_id=task_id, question=question, options=options)
        except Exception as e:  # noqa: BLE001
            logger.exception("[Scheduler] Planning phase FAILED")
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
        while True:
            failed = False
            for phase in plan.phases:
                logger.info("[Scheduler] ── Phase %d: %s ──", phase.phase_order, phase.phase_name)
                for step in phase.steps:
                    exec_order += 1
                    ctx = ExecutionContext(
                        plan=plan,
                        current_phase_id=phase.phase_id,
                        current_step=step,
                        global_context=self.context.global_context,
                    )
                    trace = self.executor.execute_step(ctx, exec_order)
                    traces.append(trace)
                    if trace.step_result.status == "failed":
                        directive = self._gather_recovery_directive(step, trace, ctx)
                        if directive and directive.action == "replan" and replans < self.config.max_replans:
                            replans += 1
                            logger.info("[Scheduler] Replanning (attempt %d) due to %s", replans, directive.failure_type)
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

        elapsed = time.time() - t_start
        logger.info("[Scheduler] ══ Task done ══ id=%s answer=%s success=%s elapsed=%.2fs",
                     task_id, answer, success, elapsed)
        logger.info("=" * 60)

        return FinalResult(
            task_id=task_id,
            answer=answer,
            success=success,
            plan=plan,
            traces=traces,
            elapsed_sec=elapsed,
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
