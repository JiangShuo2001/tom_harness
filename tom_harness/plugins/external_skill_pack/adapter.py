"""SkillPackAdapter — ABC.

A SkillPackAdapter is the single contract the harness uses to consume a
skill set authored elsewhere. The contract is intentionally minimal:

    pack = SomeAdapter(<config>)
    pack.load_into(skill_lib)               # populate our SkillLib
    skill_id = pack.route(question, story, options)   # choose one skill
    info = pack.metadata()                  # provenance for logging

Adapters must NOT modify the wrapped pack's source files. They MAY
translate file formats (e.g. a Python prompt-string → SKILL.md), but the
external content stays canonical at its origin.

Routing modes are pack-defined; common values are "static", "signature",
"llm". The runner asks the adapter for `route(...)`; how that's
computed is the adapter's business.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillPackInfo:
    """Provenance / introspection summary returned by metadata()."""
    pack_name: str                         # short label (e.g. "set1", "set2")
    contributor: str                       # author of the pack
    pack_version: str                      # version string (or path mtime)
    n_skills: int                          # how many skill prompts were loaded
    skill_ids: list[str] = field(default_factory=list)
    routing_mode: str = "unknown"          # "static" | "signature" | "llm" | ...
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingResult:
    """Output of `adapter.route(...)`. None skill_id means "fall through"."""
    skill_id: str | None
    confidence: float = 0.0                # adapter-defined; 0–1
    rationale: str = ""                    # short text for trace/debug
    extras: dict[str, Any] = field(default_factory=dict)


class SkillPackAdapter(ABC):
    """Base class. Concrete adapters live in sibling files."""

    @abstractmethod
    def load_into(self, skill_lib) -> int:
        """Populate `skill_lib` with this pack's skills.

        Returns the number of skills loaded. Adapters MAY also register
        procedural handlers if the pack supplies them.
        """
        ...

    @abstractmethod
    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RoutingResult:
        """Pick a skill for this case (or return None to skip the pack)."""
        ...

    @abstractmethod
    def metadata(self) -> SkillPackInfo:
        """Provenance summary."""
        ...

    # ── optional convenience hooks (non-abstract) ────────────────────────
    def describe_skill_ids(self) -> list[str]:
        """Adapters may override to list visible skills cheaply."""
        return self.metadata().skill_ids
