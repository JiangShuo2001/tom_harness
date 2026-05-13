"""SkillV4Router — LLM-based router over 22 skills from skills_v4."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ..llm import LLMClient
from .base import Router, RouteDecision

logger = logging.getLogger(__name__)

_DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "skills_v4"


@dataclass
class SkillV4Router(Router):
    """Routes a ToM question to one of 22 skills via a single LLM call."""

    llm: LLMClient
    skills_dir: Path = _DEFAULT_SKILLS_DIR

    def __post_init__(self) -> None:
        from tom_harness.tools.skills_v4 import llm_router
        self._router_mod = llm_router

    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision:
        opts = options or {}
        labels = list(opts.keys())
        values = list(opts.values())

        prompt = self._router_mod.build_router_prompt(
            story=story,
            question=question,
            options=values,
            labels=labels,
        )

        try:
            resp = self.llm.chat(
                "You are a skill router. Output only the skill ID.",
                prompt,
                max_tokens=64,
            )
        except Exception as e:
            logger.warning("[SkillV4Router] LLM call failed: %s", e)
            return RouteDecision(skill_id=None, rationale=f"LLM error: {e}")

        skill_id = self._router_mod.parse_router_choice(resp)
        if skill_id is None or skill_id == "NONE":
            return RouteDecision(skill_id=None, rationale=f"router chose NONE (raw: {resp.strip()[:80]})")

        logger.info("[SkillV4Router] Routed to: %s (raw: %s)", skill_id, resp.strip()[:80])
        return RouteDecision(skill_id=skill_id, rationale=f"router chose {skill_id}")

    def get_skill_body(self, skill_id: str) -> str | None:
        """Return the full SKILL.md body (without frontmatter) for the given skill."""
        return self._router_mod.get_skill_prompt(skill_id)
