"""tom_harness — ToM Agent Harness.

CANONICAL single-shot path (use this by default):
  runtime.HarnessRuntime
    · Router      — routing/ (SkillV4Router or OraclePicksRouter)
    · RAGv2Engine — tools/rag_v2.py (optional, category-aware retrieval)
    · Validators  — validators/ (e.g. ScalarProceduralValidator)
  One LLM call per sample, optional validator-driven retry.

LEGACY Plan/Execute path (kept for research scenarios):
  Scheduler -> Planner -> Executor -> Tool Layer
"""

# ── Canonical (single-shot) ────────────────────────────────────────────────
from .llm import LLMClient
from .runtime import HarnessRuntime, RuntimeResult, build_default_runtime
from .routing import Router, RouteDecision, OraclePicksRouter, SkillV4Router
from .validators import Validator, ValidationResult, ScalarProceduralValidator

# ── Legacy (Plan/Execute) — kept for back-compat, not recommended for ToMBench
from .schemas import (
    Plan, Phase, Step, ToolCall, ToolType,
    ExecutionTrace, Memory, ExecutionContext, FinalResult,
)
from .scheduler import Scheduler
from .planner import Planner
from .executor import Executor
from .registry import ToolRegistry
from .context import ContextManager

__all__ = [
    # canonical
    "LLMClient", "HarnessRuntime", "RuntimeResult", "build_default_runtime",
    "Router", "RouteDecision", "OraclePicksRouter", "SkillV4Router",
    "Validator", "ValidationResult", "ScalarProceduralValidator",
    # legacy
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager",
]
__version__ = "0.5.0"
