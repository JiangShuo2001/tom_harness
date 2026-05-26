"""Router abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RouteDecision:
    """Output of `router.route(...)`. None skill_id means "no skill, raw LLM"."""
    skill_id: str | None
    skill_ids: list[str] = field(default_factory=list)
    rationale: str = ""
    n_llm_calls: int = 0


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


class NoOpRouter(Router):
    """Always returns no skill — pure raw LLM baseline."""

    def route(self, *, question: str, story: str = "",
              options: dict[str, str] | None = None,
              task_type: str | None = None) -> RouteDecision:
        return RouteDecision(skill_id=None, rationale="no-op")
