"""Hook / plugin registration.

Plugins register callbacks at named extension points. The core never knows
what the plugins do — it just fires events and collects their results.

Extension points currently supported:
  - before_plan       (inputs: question, task_type)  → optional preamble text
  - after_plan        (inputs: plan)                   → optional amended plan
  - before_step       (inputs: step, context)          → side effects only
  - after_step        (inputs: step, trace, context)   → side effects only
  - on_step_failure   (inputs: step, trace, context)   → RecoveryDirective | None
  - before_finalize   (inputs: accumulated_results)    → side effects only
  - enrich_memory     (inputs: memory)                  → Memory (may annotate)

Plugins can inspect/mutate context but should NOT bypass the scheduler.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RecoveryDirective:
    """A plugin's advice to the scheduler after a step failure."""
    action: str                 # "retry" | "replan" | "skip" | "abort"
    failure_type: str = ""      # plugin-defined label (e.g. "knowledge_gate_bypass")
    inject_skills: list[str] = field(default_factory=list)
    note: str = ""


Hook = Callable[..., Any]


@dataclass
class HookRegistry:
    """Named multi-callback registry."""
    _hooks: dict[str, list[Hook]] = field(default_factory=lambda: defaultdict(list))

    def register(self, event: str, fn: Hook) -> None:
        self._hooks[event].append(fn)

    def fire(self, event: str, *args: Any, **kwargs: Any) -> list[Any]:
        """Fire all callbacks for an event, collecting non-None return values."""
        results: list[Any] = []
        for fn in self._hooks.get(event, []):
            try:
                r = fn(*args, **kwargs)
                if r is not None:
                    results.append(r)
            except Exception as e:  # noqa: BLE001
                # A misbehaving plugin should not crash the harness
                import logging
                logging.getLogger(__name__).warning(
                    f"Hook {event} callback {fn} raised: {e}"
                )
        return results
