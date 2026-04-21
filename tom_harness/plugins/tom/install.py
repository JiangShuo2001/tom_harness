"""One-call ToM plugin installer.

Attaches ToM-specific behavior to an already-constructed harness.
Keeps core code untouched — this file is the only wiring point.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...hooks import HookRegistry
from ...tools.skills import SkillLib
from . import failure_handlers, memory_index, validators


@dataclass
class ToMInstallation:
    """Record of what was installed — useful for debugging and tests."""
    hooks_registered: list[str]
    plan_templates_loaded: int
    failure_taxonomy_size: int


def install(
    *,
    hooks: HookRegistry,
    skill_lib: SkillLib,
    plan_templates_dir: Path | None = None,
) -> ToMInstallation:
    # Hooks
    hooks.register("on_step_failure", failure_handlers.on_step_failure)
    hooks.register("enrich_memory",   memory_index.enrich_memory)
    hooks.register("after_step",      validators.after_step)

    # Plan-template skills (if directory exists)
    n_templates = 0
    if plan_templates_dir and plan_templates_dir.exists():
        before = len(skill_lib.list_skills())
        skill_lib.load_dir(plan_templates_dir)
        n_templates = len(skill_lib.list_skills()) - before

    return ToMInstallation(
        hooks_registered=["on_step_failure", "enrich_memory", "after_step"],
        plan_templates_loaded=n_templates,
        failure_taxonomy_size=len(failure_handlers.FAILURE_TO_SKILLS),
    )
