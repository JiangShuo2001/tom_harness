"""Context Manager: three-tier context governance.

Tier 1 (fixed):     agent identity, tool schemas, safety policies  — cached.
Tier 2 (dynamic):   task state, retrieved memory, skill defs        — per-task.
Tier 3 (transient): single-step reasoning scratchpad                — wiped.

The manager is intentionally a thin bookkeeper: it holds references and
renders them into prompt fragments on demand. No compression heuristics
live here — those belong to plugins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import GlobalContext, Memory


@dataclass
class ContextManager:
    """Three-tier context governance with explicit scoping."""

    # Tier 1 — fixed (populated once, read many times)
    system_identity: str = ""
    tool_schema_summary: str = ""
    safety_policy: str = ""

    # Tier 1.5 — playbook (static memory, loaded once)
    playbook_content: str = ""

    # Tier 1.6 — injected skill / RAG context (per-task, set by Scheduler)
    skill_content: str = ""
    rag_context: str = ""

    # Tier 2 — dynamic (per-task, mutated during run)
    global_context: GlobalContext | None = None

    # Tier 3 — transient (per-step, cleared after each step)
    transient: dict[str, Any] = field(default_factory=dict)

    def install_playbook(self, content: str) -> None:
        self.playbook_content = content

    def install_skill(self, content: str) -> None:
        self.skill_content = content

    def install_rag_context(self, content: str) -> None:
        self.rag_context = content

    def install_fixed(
        self,
        *,
        system_identity: str,
        tool_schema_summary: str,
        safety_policy: str = "",
    ) -> None:
        self.system_identity = system_identity
        self.tool_schema_summary = tool_schema_summary
        self.safety_policy = safety_policy

    def begin_task(self, question: str, options: dict[str, str] | None = None) -> GlobalContext:
        self.global_context = GlobalContext(
            original_question=question,
            original_options=options or {},
        )
        self.transient.clear()
        self.skill_content = ""
        self.rag_context = ""
        return self.global_context

    def attach_memories(self, memories: list[Memory]) -> None:
        assert self.global_context is not None
        self.global_context.memory_retrieved = memories

    def attach_skill_defs(self, skill_defs: list[dict[str, Any]]) -> None:
        assert self.global_context is not None
        self.global_context.skill_definitions = skill_defs

    def record_step_result(self, phase_name: str, variable_name: str, value: Any) -> None:
        assert self.global_context is not None
        phase_dict = self.global_context.accumulated_results.setdefault(phase_name, {})
        phase_dict[variable_name] = value

    def clear_transient(self) -> None:
        self.transient.clear()

    def render_fixed_preamble(self) -> str:
        parts = []
        if self.system_identity:
            parts.append(f"## Agent Identity\n{self.system_identity}")
        if self.tool_schema_summary:
            parts.append(f"## Available Tools\n{self.tool_schema_summary}")
        if self.safety_policy:
            parts.append(f"## Safety\n{self.safety_policy}")
        return "\n\n".join(parts)

    def render_dynamic_state(self, *, include_accumulated: bool = True) -> str:
        if self.global_context is None:
            return ""
        parts = [f"## Current Question\n{self.global_context.original_question}"]
        if self.global_context.original_options:
            opts = "\n".join(f"{k}. {v}" for k, v in self.global_context.original_options.items() if v)
            parts.append(f"## Options\n{opts}")
        if self.global_context.memory_retrieved:
            mem_lines = [
                f"- [{m.memory_id[:8]}] ({m.task.task_type}) task: {m.task.question[:120]}"
                for m in self.global_context.memory_retrieved
            ]
            parts.append("## Retrieved Memories\n" + "\n".join(mem_lines))
        if self.global_context.skill_definitions:
            sk_lines = [
                f"- {s.get('skill_id', '?')}: {s.get('description', '')[:160]}"
                for s in self.global_context.skill_definitions
            ]
            parts.append("## Available Skills\n" + "\n".join(sk_lines))
        if include_accumulated and self.global_context.accumulated_results:
            acc_parts = []
            for phase_name, step_results in self.global_context.accumulated_results.items():
                acc_parts.append(f"### {phase_name}")
                for k, v in step_results.items():
                    acc_parts.append(f"- {k}: {str(v)}")
            parts.append("## Accumulated Step Results\n" + "\n".join(acc_parts))
        if self.skill_content:
            parts.append(f"## Strategy Guide\n{self.skill_content}")
        if self.rag_context:
            parts.append(f"## Retrieved Knowledge\n{self.rag_context}")
        return "\n\n".join(parts)
