"""Skill Library.

Skills are Markdown documents (Anthropic/Vercel SKILL.md format) plus
optional Python handlers. The library exposes two tool surfaces:

  - `skill_list`    : planner-facing, returns lightweight skill index
  - `execute_skill` : executor-facing, runs a named skill on given context

A skill is either:
  (a) **Declarative** — an SKILL.md with frontmatter + workflow; execution
      is performed by the LLM against the skill text as a guidance prompt.
  (b) **Procedural**  — an SKILL.md plus a Python callable registered at
      load time; execution calls the handler directly (for deterministic
      procedures like regex extraction, metadata enrichment, etc.).

Skills are discovered from a directory; plugins contribute by dropping
files or calling `register_handler`.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..schemas import ToolType
from .base import Tool

logger = logging.getLogger(__name__)

_FRONTMATTER = re.compile(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$", re.MULTILINE)


@dataclass
class SkillRecord:
    skill_id: str
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    body: str = ""
    handler: Callable[..., Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillLib:
    """Directory-based skill index with optional Python handlers."""

    skills_dir: Path | None = None
    _skills: dict[str, SkillRecord] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.skills_dir and self.skills_dir.exists():
            self.load_dir(self.skills_dir)

    # ── Tool interface ─────────────────────────────────────────────────────
    @property
    def tool_type(self) -> ToolType:
        return ToolType.SKILL

    @property
    def tool_name(self) -> str:
        # Default surface; `skill_list` is exposed via a sibling tool (see below)
        return "execute_skill"

    @property
    def description(self) -> str:
        return "Execute a named skill on the given input context. Params: skill_id:str, input_context:dict, llm_fn:callable (provided by executor)"

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        out = dict(params)
        if "skill_id" not in out:
            raise ValueError("execute_skill requires `skill_id`")
        out.setdefault("input_context", {})
        return out

    def run(
        self,
        *,
        skill_id: str,
        input_context: dict[str, Any],
        llm_fn: Callable[[str, str], str] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        rec = self._skills.get(skill_id)
        if rec is None:
            raise KeyError(f"Unknown skill: {skill_id}")
        # Procedural path: deterministic Python
        if rec.handler is not None:
            result = rec.handler(**input_context)
            return {"skill_id": skill_id, "mode": "procedural", "result": result}
        # Declarative path: LLM-guided
        if llm_fn is None:
            raise RuntimeError(
                f"Skill {skill_id} is declarative but no llm_fn was provided"
            )
        system = (
            "You are executing a ToM reasoning skill. Follow the skill's "
            "workflow section strictly and return a concise structured result."
        )
        user = (
            f"## Skill\n{rec.body}\n\n"
            f"## Input Context\n{input_context}\n\n"
            "## Task\nApply the skill to the input and output the structured "
            "result as a JSON object on a single line."
        )
        response = llm_fn(system, user)
        return {"skill_id": skill_id, "mode": "declarative", "raw_response": response}

    # ── Directory / handler loading ────────────────────────────────────────
    def load_dir(self, path: Path) -> None:
        for f in sorted(path.glob("*.md")):
            try:
                rec = self._parse_skill_file(f)
                self._skills[rec.skill_id] = rec
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to parse skill {f.name}: {e}")

    def register_handler(
        self,
        skill_id: str,
        handler: Callable[..., Any],
        *,
        name: str | None = None,
        description: str = "",
        triggers: list[str] | None = None,
    ) -> None:
        if skill_id in self._skills:
            self._skills[skill_id].handler = handler
        else:
            self._skills[skill_id] = SkillRecord(
                skill_id=skill_id,
                name=name or skill_id,
                description=description,
                triggers=triggers or [],
                handler=handler,
            )

    def list_skills(self) -> list[dict[str, Any]]:
        return [
            {
                "skill_id": r.skill_id,
                "name": r.name,
                "description": r.description,
                "triggers": r.triggers,
                "has_handler": r.handler is not None,
                "metadata": r.metadata,
            }
            for r in self._skills.values()
        ]

    def get(self, skill_id: str) -> SkillRecord | None:
        return self._skills.get(skill_id)

    # ── internals ──────────────────────────────────────────────────────────
    @staticmethod
    def _parse_skill_file(path: Path) -> SkillRecord:
        text = path.read_text(encoding="utf-8")
        m = _FRONTMATTER.match(text)
        if not m:
            # No frontmatter → use filename as id, full text as body
            return SkillRecord(
                skill_id=path.stem,
                name=path.stem,
                description="",
                body=text,
            )
        front_raw, body = m.group(1), m.group(2)
        front = _parse_simple_yaml(front_raw)
        return SkillRecord(
            skill_id=front.get("skill_id") or front.get("name") or path.stem,
            name=front.get("name", path.stem),
            description=front.get("description", ""),
            triggers=front.get("triggers", []) if isinstance(front.get("triggers"), list) else [],
            body=body.strip(),
            metadata={k: v for k, v in front.items() if k not in {"skill_id", "name", "description", "triggers"}},
        )


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Tiny YAML subset: `key: value` lines and `key:\\n  - item` lists.

    Good enough for SKILL.md frontmatter without pulling in PyYAML.
    """
    out: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list_key is not None:
            out.setdefault(current_list_key, []).append(line[4:].strip().strip('"').strip("'"))
            continue
        current_list_key = None
        if ":" in line:
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if not v:
                current_list_key = k
                out[k] = []
            else:
                out[k] = v.strip('"').strip("'")
    return out
