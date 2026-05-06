"""Router abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RouteDecision:
    """Output of `router.route(...)`. None skill_id means "no skill, raw LLM"."""
    skill_id: str | None
    rationale: str = ""


class Router(ABC):
    """Route a sample to a skill_id.

    Implementations may use LLM calls (e.g. SkillV4Router) or pure
    lookup tables (e.g. OraclePicksRouter).
    """

    @abstractmethod
    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision: ...
