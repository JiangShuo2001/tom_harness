"""tom_harness — ToM Agent Harness.

CANONICAL single-shot path (use this by default):
  runtime.HarnessRuntime
    · Router      — routing/ (SkillV5Router, SkillV4Router, or OraclePicksRouter)
    · RAGv2Engine — tools/rag_v2.py (optional, category-aware retrieval)
    · Validators  — validators/ (e.g. ScalarProceduralValidator)
  One LLM call per sample, optional validator-driven retry.

LEGACY Plan/Execute path (moved to tom_harness/legacy/):
  Scheduler -> Planner -> Executor -> Tool Layer
  Import via: from tom_harness.legacy import Scheduler, Planner, ...
"""

# ── Canonical (single-shot) ────────────────────────────────────────────────
from .llm import LLMClient
from .runtime import HarnessRuntime, RuntimeResult, build_default_runtime
from .routing import Router, RouteDecision, OraclePicksRouter, SkillV4Router
from .validators import Validator, ValidationResult, ScalarProceduralValidator

# ── Legacy (Plan/Execute) — re-exported for backward compatibility ─────────
# Prefer importing directly from tom_harness.legacy instead.
from .legacy import (
    Plan, Phase, Step, ToolCall, ToolType,
    ExecutionTrace, Memory, ExecutionContext, FinalResult,
    Scheduler, Planner, Executor,
    ToolRegistry, ContextManager,
)

__all__ = [
    # canonical
    "LLMClient", "HarnessRuntime", "RuntimeResult", "build_default_runtime",
    "Router", "RouteDecision", "OraclePicksRouter", "SkillV4Router",
    "Validator", "ValidationResult", "ScalarProceduralValidator",
    # legacy (re-exported)
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager",
]
__version__ = "0.6.0"
