"""Planner Agent.

Responsibility: turn a question into a structured multi-phase Plan.

Protocol (from the system spec):
  1. MUST query Memory Store before producing a plan (mandatory warm-start).
  2. Produces a Plan conforming to schemas.Plan.
  3. Tool selections in the plan must reference names the Tool Registry
     can resolve.

Design notes
------------
- Planning is one LLM call. The returned JSON is validated against the
  Pydantic schema; on failure we allow one repair pass.
- Retrieved memories are passed both as context to the LLM and attached
  to the Plan's `memory_references` field for auditability.
- Task-type classification is delegated to the LLM as part of planning;
  plugins that want specialized flows can post-process via the
  `after_plan` hook.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from .context import ContextManager
from .hooks import HookRegistry
from .llm import LLMClient
from .registry import ToolRegistry
from .schemas import (
    ExpectedFinalOutput, Memory, MemoryReference, Phase, Plan, Step, ToolCall, ToolType,
)
from .tools.memory import MemoryStore

logger = logging.getLogger(__name__)


PLANNER_SYSTEM = """You are the Planner of a Theory-of-Mind agent harness. \
Your job: decompose the question into a multi-phase Plan that the Executor \
can follow step by step. Obey the JSON schema exactly.

Principles:
- Prefer 2-4 phases with 1-3 steps each; keep plans lean.
- Each step may call at most one tool. Use `"tool_type": "none"` if the \
step is pure reasoning.
- Every tool name you mention MUST be one of those listed in AVAILABLE TOOLS.
- When retrieved memories are provided, prefer matching their plan structure \
if task_type aligns.
- `task_type` should be a short snake_case label describing the ToM \
reasoning category (e.g. false_belief, second_order_belief, \
knowledge_gate, aware_of_reader, faux_pas, scalar_implicature, hidden_emotion, \
pragmatic_inference, perspective_taking, or general_tom).
- Output ONLY a JSON object matching the schema. No commentary."""


PLANNER_USER_TEMPLATE = """## Context
{fixed_preamble}

## Retrieved Memories (from warm-start Memory Store query)
{memory_block}

## Current Question
{question}

{options_block}

## Output Schema
Return a JSON object with this shape (field descriptions are for you, \
do not include them in output):

{{
  "task_type": "<snake_case ToM category>",
  "expected_final_output": {{
    "format": "letter",
    "description": "single letter A/B/C/D"
  }},
  "phases": [
    {{
      "phase_name": "<short>",
      "phase_order": 1,
      "description": "<what this phase accomplishes>",
      "steps": [
        {{
          "step_order": 1,
          "description": "<action for this step>",
          "depends_on": [],
          "tool": {{
            "tool_type": "memory|skill|rag|none",
            "tool_name": "<exact name from AVAILABLE TOOLS or empty>",
            "tool_params": {{ ... }}
          }},
          "expected_output_schema": "<what this step should yield>"
        }}
      ]
    }}
  ]
}}

Generate the plan now."""


@dataclass
class Planner:
    """Produces a Plan from a question, mandatorily consulting Memory first."""

    llm: LLMClient
    registry: ToolRegistry
    context: ContextManager
    hooks: HookRegistry
    memory: MemoryStore
    memory_top_k: int = 3
    memory_similarity_threshold: float = 0.0
    task_id_prefix: str = "task"

    def plan(self, *, task_id: str, question: str, options: dict[str, str] | None = None) -> Plan:
        # 1. Pre-plan hooks (plugins may inject preamble text, etc.)
        self.hooks.fire("before_plan", question=question)

        # 2. MANDATORY Memory Store warm-start
        retrieval = self.memory.run(
            query=question,
            top_k=self.memory_top_k,
            similarity_threshold=self.memory_similarity_threshold,
        )
        retrieved_memories: list[Memory] = []
        memory_refs: list[MemoryReference] = []
        for hit in retrieval["memories"]:
            m = Memory(**hit["full_memory"])
            retrieved_memories.append(m)
            memory_refs.append(MemoryReference(
                memory_id=m.memory_id,
                similarity_score=hit["similarity_score"],
                task_description=m.task.question[:200],
                plan_summary=hit["plan_summary"],
            ))
        self.context.attach_memories(retrieved_memories)

        # 3. LLM plan generation
        memory_block = _format_memory_block(memory_refs, retrieved_memories)
        options_block = ""
        if options:
            opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
            options_block = f"## Options\n{opts}\n"

        user = PLANNER_USER_TEMPLATE.format(
            fixed_preamble=self.context.render_fixed_preamble(),
            memory_block=memory_block,
            question=question,
            options_block=options_block,
        )

        plan_dict = self._generate_plan_json(user)
        plan = self._assemble_plan(task_id=task_id, plan_dict=plan_dict, memory_refs=memory_refs)

        # 4. Post-plan hooks (plugins may amend the plan)
        amendments = self.hooks.fire("after_plan", plan=plan)
        for amended in amendments:
            if isinstance(amended, Plan):
                plan = amended

        return plan

    # ── internals ──────────────────────────────────────────────────────────
    def _generate_plan_json(self, user: str) -> dict[str, Any]:
        try:
            return self.llm.chat_json(PLANNER_SYSTEM, user, max_tokens=4096)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"First plan generation failed: {e}; attempting repair pass")
            repair_user = user + "\n\nYour previous response did not parse as JSON. Output ONLY the JSON object, no prose, no fences."
            return self.llm.chat_json(PLANNER_SYSTEM, repair_user, max_tokens=4096)

    def _assemble_plan(
        self,
        *,
        task_id: str,
        plan_dict: dict[str, Any],
        memory_refs: list[MemoryReference],
    ) -> Plan:
        raw_phases = plan_dict.get("phases", [])
        phases: list[Phase] = []
        for i, rp in enumerate(raw_phases, 1):
            steps: list[Step] = []
            for j, rs in enumerate(rp.get("steps", []), 1):
                tool = None
                rt = rs.get("tool")
                if rt and rt.get("tool_type", "none") != "none":
                    try:
                        tool = ToolCall(
                            tool_type=ToolType(rt["tool_type"]),
                            tool_name=rt.get("tool_name", ""),
                            tool_params=rt.get("tool_params", {}) or {},
                        )
                        # B9 fix: validate tool_name against registry at plan
                        # assembly time, not execution time. Unknown tools
                        # become tool=None (effectively a pure-reasoning step)
                        # so the executor doesn't waste a dispatch on a name
                        # that will fail.
                        if tool and not self.registry.has(tool.tool_type, tool.tool_name):
                            logger.warning(
                                f"Planner emitted unknown tool ({tool.tool_type.value}, "
                                f"{tool.tool_name}) — converting step to pure-reasoning"
                            )
                            tool = None
                    except ValueError:
                        tool = None  # unknown tool_type — drop it
                deps_raw = rs.get("depends_on", []) or []
                deps = [str(d) for d in deps_raw] if isinstance(deps_raw, list) else []
                eos_raw = rs.get("expected_output_schema")
                eos = None if eos_raw is None else (eos_raw if isinstance(eos_raw, str) else json.dumps(eos_raw, ensure_ascii=False))
                steps.append(Step(
                    step_order=int(rs.get("step_order", j) or j),
                    description=str(rs.get("description", "")),
                    depends_on=deps,
                    tool=tool,
                    expected_output_schema=eos,
                ))
            phases.append(Phase(
                phase_name=rp.get("phase_name", f"Phase {i}"),
                phase_order=rp.get("phase_order", i),
                description=rp.get("description", ""),
                steps=steps,
            ))
        efo_raw = plan_dict.get("expected_final_output") or {"format": "letter", "description": "single letter"}
        return Plan(
            task_id=task_id,
            task_type=plan_dict.get("task_type", "general_tom"),
            memory_references=memory_refs,
            phases=phases,
            expected_final_output=ExpectedFinalOutput(**efo_raw),
        )


def _format_memory_block(refs: list[MemoryReference], mems: list[Memory]) -> str:
    if not refs:
        return "(no similar tasks in memory yet — this is a cold start)"
    lines = []
    for ref, mem in zip(refs, mems):
        lines.append(
            f"- [{ref.memory_id[:8]}] similarity={ref.similarity_score:.3f} "
            f"type={mem.task.task_type}\n"
            f"  question: {ref.task_description[:160]}\n"
            f"  plan: {ref.plan_summary}"
        )
    return "\n".join(lines)
