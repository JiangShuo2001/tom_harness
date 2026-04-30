"""Set2 adapter — wraps the 12-skill pack with LLM router.

Pack origin: /workspace/symbolictom_report/skill_set2/skill_v2/
Layout    : skills.py (12 SKILL_S* prompt strings + SKILL_TARGETS),
             llm_router.py (ROUTER_CATALOG + LLM-based router).
Routing   : two modes —
             - "llm"        : call their llm_router.route() (one extra LLM call)
             - "signature"  : use SKILL_TARGETS table keyed on task_type

This file does NOT modify the pack. We import their `skills` and
`llm_router` modules via sys.path; if their module names collide with
our own (`tom_harness.tools.skills`), we use a sandboxed import.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ...tools.skills import SkillLib, SkillRecord
from .adapter import RoutingResult, SkillPackAdapter, SkillPackInfo


def _sandbox_import(module_name: str, file_path: Path):
    """Import a Python file under a custom name, isolated from sys.path
    collisions with our package. Uses spec.loader directly so the file's
    `import skills` is resolved within the same directory.
    """
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass
class Set2Adapter(SkillPackAdapter):
    """Wraps skill_set2 pack."""

    pack_root: Path = Path(__file__).resolve().parent / "data" / "skill_set2"
    routing_mode: str = "llm"              # "llm" | "signature"
    router_llm_fn: Callable[[str, str], str] | None = None     # adapter caller supplies
    _skills_module: Any = field(default=None, init=False)
    _router_module: Any = field(default=None, init=False)
    _loaded_ids: list[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        # Both files import each other (`from skills import SKILLS`); we must
        # ensure the directory is importable as the canonical name.
        sys.path.insert(0, str(self.pack_root))
        _MISSING = object()
        prev_skills = sys.modules.get("skills", _MISSING)
        # Import order matters: skills first (router imports skills)
        try:
            self._skills_module = _sandbox_import("set2_skills", self.pack_root / "skills.py")
            sys.modules["skills"] = self._skills_module    # router does `from skills import SKILLS`
            self._router_module = _sandbox_import("set2_router", self.pack_root / "llm_router.py")
        finally:
            # Restore the previous "skills" entry (or remove it if absent before).
            if prev_skills is _MISSING:
                sys.modules.pop("skills", None)
            else:
                sys.modules["skills"] = prev_skills
            try:
                sys.path.remove(str(self.pack_root))
            except ValueError:
                pass

    # ─── load skills into our SkillLib ─────────────────────────────────
    def load_into(self, skill_lib: SkillLib) -> int:
        sk = self._skills_module
        # set2 exposes a SKILLS dict mapping S<id> → prompt string. The
        # exact attribute name may vary; probe common ones.
        skills_dict = None
        for attr_name in ("SKILLS", "ALL_SKILLS", "SKILL_PROMPTS"):
            if hasattr(sk, attr_name):
                skills_dict = getattr(sk, attr_name)
                break
        if skills_dict is None:
            # Fallback: scan for SKILL_S* string constants
            skills_dict = {
                k.replace("SKILL_", ""): v
                for k, v in vars(sk).items()
                if k.startswith("SKILL_S") and isinstance(v, str)
            }
        loaded = 0
        for skill_id_raw, prompt_text in skills_dict.items():
            external_id = str(skill_id_raw)                # e.g. "S1_FauxPas"
            new_skill_id = f"cs2_{external_id}"             # namespaced
            # First non-empty line of the prompt as a description
            first_line = next((l for l in prompt_text.splitlines() if l.strip()), "")
            rec = SkillRecord(
                skill_id=new_skill_id,
                name=external_id,
                description=first_line.strip()[:200],
                triggers=[],
                body=prompt_text,
                metadata={"contributor_pack": "set2", "external_id": external_id,
                          "external_path": str(self.pack_root / "skills.py")},
            )
            skill_lib._skills[new_skill_id] = rec
            self._loaded_ids.append(new_skill_id)
            loaded += 1
        return loaded

    # ─── routing ───────────────────────────────────────────────────────
    def route(
        self, *, question: str, story: str = "",
        options: dict[str, str] | None = None, task_type: str | None = None,
    ) -> RoutingResult:
        if self.routing_mode == "signature" and task_type is not None:
            return self._route_via_targets(task_type)
        if self.routing_mode == "llm":
            return self._route_via_llm(question=question, story=story, options=options)
        return RoutingResult(skill_id=None, confidence=0.0, rationale="set2: no routing mode active")

    def _route_via_targets(self, task_type: str) -> RoutingResult:
        sk = self._skills_module
        targets = getattr(sk, "SKILL_TARGETS", None) or {}
        for skill_id, target_list in targets.items():
            if any(task_type.lower() == t.lower() or task_type.lower() in t.lower() for t in target_list):
                return RoutingResult(
                    skill_id=f"cs2_{skill_id}", confidence=0.9,
                    rationale=f"set2 SKILL_TARGETS[{skill_id}] matched task_type={task_type}",
                )
        return RoutingResult(skill_id=None, confidence=0.0, rationale="set2: no SKILL_TARGETS match")

    def _route_via_llm(
        self, question: str, story: str, options: dict[str, str] | None,
    ) -> RoutingResult:
        if self.router_llm_fn is None:
            return RoutingResult(skill_id=None, rationale="set2 LLM router: no llm_fn provided")
        rt = self._router_module
        # Build their prompt and parse their output
        item = {"story": story, "question": question, "options": options or {}}
        try:
            prompt = rt.build_router_prompt(item) if hasattr(rt, "build_router_prompt") else None
        except Exception as e:  # noqa: BLE001
            return RoutingResult(skill_id=None, rationale=f"set2 prompt build failed: {e}")
        if prompt is None:
            # Fallback: minimal prompt mimicking their format
            catalog_lines = [
                f"- {sid}: {desc}" for sid, desc in rt.ROUTER_CATALOG.items()
            ]
            prompt = (
                "Pick ONE skill id from the list (or NONE) for this case. "
                "Reply on a single line: `Skill: <ID>`.\n\n"
                f"## Catalog\n" + "\n".join(catalog_lines) + "\n\n"
                f"## Story\n{story}\n\n## Question\n{question}\n\n"
                f"## Options\n" + "\n".join(f"{k}. {v}" for k, v in (options or {}).items())
            )
        # System instruction (theirs)
        sys_msg = getattr(rt, "ROUTER_INSTRUCTION", "Pick one skill id and reply `Skill: <ID>`.")
        try:
            raw = self.router_llm_fn(sys_msg, prompt)
        except Exception as e:  # noqa: BLE001
            return RoutingResult(skill_id=None, rationale=f"set2 LLM call failed: {e}")
        # Parse with their own parser if available
        choice = None
        if hasattr(rt, "parse_router_choice"):
            try:
                choice = rt.parse_router_choice(raw)
            except Exception:  # noqa: BLE001
                pass
        if not choice:
            m = re.search(r"\bSkill\s*:\s*([A-Z][A-Za-z0-9_]+|NONE)\b", raw or "")
            choice = m.group(1) if m else None
        if not choice or choice.upper() == "NONE":
            return RoutingResult(skill_id=None, confidence=0.5, rationale=f"set2 LLM router → NONE ({raw[:60]!r})")
        return RoutingResult(
            skill_id=f"cs2_{choice}", confidence=0.7,
            rationale=f"set2 LLM router picked {choice}",
            extras={"raw_response": raw[:200]},
        )

    # ─── metadata ───────────────────────────────────────────────────────
    def metadata(self) -> SkillPackInfo:
        return SkillPackInfo(
            pack_name="set2",
            contributor="teammate-B",
            pack_version=str(self.pack_root.stat().st_mtime_ns) if self.pack_root.exists() else "missing",
            n_skills=len(self._loaded_ids),
            skill_ids=list(self._loaded_ids),
            routing_mode=self.routing_mode,
            extras={"pack_root": str(self.pack_root),
                    "router_module_loaded": self._router_module is not None},
        )
