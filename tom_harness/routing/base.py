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
    """Pure-function router: (question, story, options, task_type) -> RouteDecision.

    Routers MUST NOT make LLM calls. If the routing decision needs LLM
    judgment, do it offline once and encode the rules.
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
