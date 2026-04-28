"""One-call ToM plugin installer.

Attaches ToM-specific behavior to an already-constructed harness.
Keeps core code untouched — this file is the only wiring point.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ...hooks import HookRegistry
from ...tools.skills import SkillLib
from . import failure_handlers, memory_index, validators
from .skills import register_all as register_procedural_handlers


_PLUGIN_ROOT = Path(__file__).resolve().parent


@dataclass
class ToMInstallation:
    """Record of what was installed — useful for debugging and tests."""
    hooks_registered: list[str] = field(default_factory=list)
    plan_templates_loaded: int = 0
    skills_loaded: int = 0
    procedural_handlers: int = 0
    failure_taxonomy_size: int = 0


def install(
    *,
    hooks: HookRegistry,
    skill_lib: SkillLib,
    plan_templates_dir: Path | None = None,
    skills_dir: Path | None = None,
) -> ToMInstallation:
    """Install ToM plugin into an existing harness.

    Parameters
    ----------
    hooks : HookRegistry
        Shared hook registry that the Scheduler/Planner/Executor use.
    skill_lib : SkillLib
        The skill library to populate. Can be empty; both plan templates
        and reasoning skills will be loaded into it.
    plan_templates_dir : Path | None
        Directory of plan-template SKILL.md files. Defaults to
        `plugins/tom/plan_templates/`.
    skills_dir : Path | None
        Directory of reasoning-skill SKILL.md files. Defaults to
        `plugins/tom/skills/`.
    """
    out = ToMInstallation()

    # 1. Hooks — pure plugin contributions
    hooks.register("on_step_failure", failure_handlers.on_step_failure)
    hooks.register("enrich_memory",   memory_index.enrich_memory)
    hooks.register("after_step",      validators.after_step)
    out.hooks_registered = ["on_step_failure", "enrich_memory", "after_step"]

    # 2. Plan-template skills
    ptd = plan_templates_dir or (_PLUGIN_ROOT / "plan_templates")
    if ptd.exists():
        before = len(skill_lib.list_skills())
        skill_lib.load_dir(ptd)
        out.plan_templates_loaded = len(skill_lib.list_skills()) - before

    # 3. Reasoning skills (S01–S08)
    sd = skills_dir or (_PLUGIN_ROOT / "skills")
    if sd.exists():
        before = len(skill_lib.list_skills())
        skill_lib.load_dir(sd)
        out.skills_loaded = len(skill_lib.list_skills()) - before

    # 4. Procedural handlers (e.g. S02_quantifier_solve arithmetic path)
    out.procedural_handlers = register_procedural_handlers(skill_lib)

    out.failure_taxonomy_size = len(failure_handlers.FAILURE_TO_SKILLS)
    return out
