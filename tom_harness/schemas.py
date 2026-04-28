"""Pydantic schemas for the harness.

Design principle: schemas stay generic. Every domain-specific field lives
inside `metadata: dict` slots, which plugins populate. Core code never reads
metadata — only plugins do.

Fields marked "[senior]" are from the given specification and must not be
renamed or removed. Fields marked "[ext]" are local extensions that preserve
backward compatibility while enabling plugin-based specialization.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Tool call schema
# ─────────────────────────────────────────────────────────────────────────────

class ToolType(str, Enum):
    """[senior] Allowed tool categories."""
    MEMORY = "memory"
    SKILL = "skill"
    RAG = "rag"
    NONE = "none"


class OutputMapping(BaseModel):
    """[senior] Where to store the tool's return value in ExecutionContext."""
    store_to: str = Field(..., description="Context variable name to write into")
    format: str = Field("raw", description="raw | summarized | embedded | structured | full")


class ToolCall(BaseModel):
    """[senior] Standardized tool invocation descriptor embedded in a Step."""
    tool_type: ToolType
    tool_name: str
    tool_params: dict[str, Any] = Field(default_factory=dict)
    output_mapping: OutputMapping | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Plan schema
# ─────────────────────────────────────────────────────────────────────────────

class Step(BaseModel):
    """[senior] A single execution step. Supports arbitrary-depth sub_steps."""
    step_id: str = Field(default_factory=_uuid)
    step_order: int
    description: str
    depends_on: list[str] = Field(default_factory=list)
    tool: ToolCall | None = None
    expected_output_schema: str | None = None
    sub_steps: list["Step"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)  # [ext]


class Phase(BaseModel):
    """[senior] A macro stage composed of ordered steps."""
    phase_id: str = Field(default_factory=_uuid)
    phase_name: str
    phase_order: int
    description: str
    steps: list[Step]
    metadata: dict[str, Any] = Field(default_factory=dict)  # [ext]


class MemoryReference(BaseModel):
    """[senior] Pointer to a memory consulted during planning."""
    memory_id: str
    similarity_score: float
    task_description: str
    plan_summary: str


class ExpectedFinalOutput(BaseModel):
    """[senior] Shape the executor must ultimately produce."""
    format: str
    description: str


class Plan(BaseModel):
    """[senior] The Planner's structured output."""
    plan_id: str = Field(default_factory=_uuid)
    task_id: str
    task_type: str                                           # [senior] opaque string
    created_at: str = Field(default_factory=_now)
    memory_references: list[MemoryReference] = Field(default_factory=list)
    phases: list[Phase]
    expected_final_output: ExpectedFinalOutput
    metadata: dict[str, Any] = Field(default_factory=dict)  # [ext] plugin-specific


# needed for Step self-reference
Step.model_rebuild()


# ─────────────────────────────────────────────────────────────────────────────
# Execution trace schema
# ─────────────────────────────────────────────────────────────────────────────

class Reasoning(BaseModel):
    """[senior] Executor's internal reasoning before an action."""
    thought: str
    state_analysis: str = ""
    action_rationale: str = ""


class ToolCallTrace(BaseModel):
    """[senior] Record of an actual tool invocation."""
    tool_type: str
    tool_name: str
    params: dict[str, Any]
    call_timestamp: str = Field(default_factory=_now)
    duration_ms: int = 0


class Observation(BaseModel):
    """[senior] Tool's returned output."""
    raw_output: Any = None
    structured_output: dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: str | None = None


class StepResult(BaseModel):
    """[senior] Final status line for the step."""
    status: str                          # completed | failed | skipped
    output_summary: str = ""


class ExecutionTrace(BaseModel):
    """[senior] Full audit record for a single step execution."""
    trace_id: str = Field(default_factory=_uuid)
    plan_id: str
    step_id: str
    phase_id: str
    execution_order: int
    timestamp: str = Field(default_factory=_now)
    reasoning: Reasoning
    tool_call: ToolCallTrace | None = None
    observation: Observation | None = None
    step_result: StepResult


# ─────────────────────────────────────────────────────────────────────────────
# Memory schema
# ─────────────────────────────────────────────────────────────────────────────

class TaskDescriptor(BaseModel):
    """[senior] The question/task identity stored alongside its plan."""
    task_id: str
    question: str
    task_type: str
    dataset: str = ""


class Memory(BaseModel):
    """[senior] Stored (task, plan) pair for warm-starting future planning."""
    memory_id: str = Field(default_factory=_uuid)
    task: TaskDescriptor
    plan: Plan
    execution_summary: str = ""
    success: bool = True
    score: float = 1.0
    created_at: str = Field(default_factory=_now)
    metadata: dict[str, Any] = Field(default_factory=dict)  # [ext] plugin indexing


# ─────────────────────────────────────────────────────────────────────────────
# Execution context schema
# ─────────────────────────────────────────────────────────────────────────────

class GlobalContext(BaseModel):
    """[senior] Cross-step shared state."""
    original_question: str
    original_options: dict[str, str] = Field(default_factory=dict)
    memory_retrieved: list[Memory] = Field(default_factory=list)
    skill_definitions: list[dict[str, Any]] = Field(default_factory=list)
    accumulated_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ExecutionContext(BaseModel):
    """[senior] Handed from Scheduler to Executor per step."""
    execution_id: str = Field(default_factory=_uuid)
    plan: Plan
    current_phase_id: str
    current_step: Step
    global_context: GlobalContext


# ─────────────────────────────────────────────────────────────────────────────
# Final result (run-level)
# ─────────────────────────────────────────────────────────────────────────────

class FinalResult(BaseModel):
    """Harness run output."""
    task_id: str
    answer: str
    success: bool
    plan: Plan
    traces: list[ExecutionTrace]
    elapsed_sec: float
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
