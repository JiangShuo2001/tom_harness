"""Legacy Plan/Execute pipeline.

This module contains the multi-step Plan/Execute architecture that was the
original default harness. It measured -7~9pp vs single-shot on qwen-plus
(see runtime.py docstring for context) and is no longer the recommended path
for ToMBench evaluation.

Kept here for research scenarios where multi-step reasoning is needed.

Usage:
    from tom_harness.legacy import Scheduler, Planner, Executor, ...
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
from .hooks import HookRegistry

__all__ = [
    "Plan", "Phase", "Step", "ToolCall", "ToolType",
    "ExecutionTrace", "Memory", "ExecutionContext", "FinalResult",
    "Scheduler", "Planner", "Executor",
    "ToolRegistry", "ContextManager", "HookRegistry",
]
