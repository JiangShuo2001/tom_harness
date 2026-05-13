"""One-call ToM plugin installer.

Note: In v2 migration, procedural handlers and signature-based routing
were removed. This installer now only wires hooks and loads plan templates.
Reasoning skills are loaded via SkillV4Router from tools/skills_v4/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...hooks import HookRegistry

_PLUGIN_ROOT = Path(__file__).resolve().parent


@dataclass
class ToMInstallation:
    """Record of what was installed."""
    hooks_registered: list[str] = field(default_factory=list)


def install(
    *,
    hooks: HookRegistry,
    **_kwargs,
) -> ToMInstallation:
    """Install ToM plugin hooks."""
    from . import failure_handlers, memory_index, validators

    out = ToMInstallation()
    hooks.register("on_step_failure", failure_handlers.on_step_failure)
    hooks.register("enrich_memory", memory_index.enrich_memory)
    hooks.register("after_step", validators.after_step)
    out.hooks_registered = ["on_step_failure", "enrich_memory", "after_step"]
    return out
