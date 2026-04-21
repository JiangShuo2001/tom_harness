"""tom_harness — ToM Agent Harness.

Plan-then-Execute harness with ReAct inner loop, following the architecture:
  Harness Layer (Scheduler + Tool Registry + Context Manager)
      ↓
  Planner Agent  →  Executor Agent  →  Tool Layer (Memory / Skills / RAG)

Public entry points:
  - Scheduler: top-level orchestrator
  - Planner, Executor: agent implementations
  - schemas: all Pydantic data models
"""

from .schemas import (
    Plan, Phase, Step, ToolCall, ToolType,
    ExecutionTrace, Memory, ExecutionContext, FinalResult,
)
from .scheduler import Scheduler
from .planner import Planner
from .executor import Executor
from .registry import ToolRegistry
from .context import ContextManager
from .llm import LLMClient

__all__ = [
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager", "LLMClient",
]
__version__ = "0.1.0"
