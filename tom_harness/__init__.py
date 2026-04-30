"""tom_harness — ToM Agent Harness.

Two layers, two purposes:

  1. CANONICAL single-shot path (use this by default):
       runtime.HarnessRuntime
         · Router      — routing/  (e.g. OraclePicksRouter)
         · SkillLib    — tools/skills.py (with adapters in plugins/external_skill_pack/)
         · Validators  — validators/ (e.g. ScalarProceduralValidator)
       One LLM call per sample, optional validator-driven retry.
       Empirically beats Plan/Execute on qwen-plus + ToMBench by 7-9pp.

  2. LEGACY Plan/Execute path (kept for research scenarios that need
     multi-step orchestration; not the default):
       Scheduler -> Planner -> Executor -> Tool Layer

If you are starting fresh, import from the canonical path:

    from tom_harness import LLMClient, HarnessRuntime, build_default_runtime
    from tom_harness.routing import OraclePicksRouter
    from tom_harness.tools.skills import SkillLib
    from tom_harness.plugins.external_skill_pack import Set1Adapter, Set2Adapter
"""

# ── Canonical (single-shot) ────────────────────────────────────────────────
from .llm import LLMClient
from .runtime import HarnessRuntime, RuntimeResult, build_default_runtime
from .routing import Router, RouteDecision, OraclePicksRouter
from .validators import (
    Validator, ValidationResult,
    ScalarProceduralValidator, CrossSkillValidator, FBStateBackedValidator,
)

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
    "Router", "RouteDecision", "OraclePicksRouter",
    "Validator", "ValidationResult",
    "ScalarProceduralValidator", "CrossSkillValidator", "FBStateBackedValidator",
    # legacy
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager",
]
__version__ = "0.4.0"
