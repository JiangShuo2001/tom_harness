"""Tool abstract base.

Every concrete tool declares:
  - tool_type (category: memory / skill / rag)
  - tool_name (unique within its category)
  - description (one-line summary for planner context)
  - validate_params (sanity-check and coerce inputs)
  - run (execute and return raw output)

Concrete tools MUST be side-effect-free with respect to global state
other than their own storage. They should NOT mutate ExecutionContext
directly — the executor owns that.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..schemas import ToolType


@dataclass
class ToolResult:
    """Return envelope for every tool dispatch."""
    success: bool
    raw_output: Any = None
    structured_output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0


class Tool(ABC):
    """Abstract tool interface."""

    @property
    @abstractmethod
    def tool_type(self) -> ToolType: ...

    @property
    @abstractmethod
    def tool_name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    def validate_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Validate and coerce input params. Default: pass-through."""
        return dict(params)

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Execute the tool. Raises on error. Return value is opaque."""
        ...
