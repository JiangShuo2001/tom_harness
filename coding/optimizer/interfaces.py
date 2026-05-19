"""Shared dataclasses and abstract interfaces for the Harness Optimizer.

These are intentionally minimal and *do not* import anything from the
original ``tom_harness`` package. They define the contract that
optimizer targets, policy engines, evaluators and proposers all share.

The optimizer's runtime contract is purely structural — any object that
matches the dataclass shape can be passed in. This keeps the optimizer
module independent of the ToM runtime so it can be deleted or replaced
without breaking the project.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable


# ──────────────────────────────────────────────────────────────────────
#  Routing / gating
# ──────────────────────────────────────────────────────────────────────

@dataclass
class RouteDecision:
    """Output of an EnhancedRouter (Phase 1 — UNDERSTAND).

    The optimizer keeps a *separate* RouteDecision dataclass from the
    runtime's ``tom_harness.routing.base.RouteDecision`` on purpose:
    we want to evolve scene-tag / reasoning-type / confidence semantics
    without forcing changes upstream.
    """

    skill_id: str | None = None
    scene_tag: str | None = None
    reasoning_type: str | None = None
    confidence: float = 0.0
    raw: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "scene_tag": self.scene_tag,
            "reasoning_type": self.reasoning_type,
            "confidence": self.confidence,
            "raw": dict(self.raw),
        }


@dataclass
class ModuleGateDecision:
    """Output of the route+gate policy engine (Phase 2 — GATHER)."""

    use_skill: bool = False
    use_rag: bool = False
    use_memory: bool = False
    use_validator: bool = False
    selected_validators: list[str] = field(default_factory=list)
    rationale: str = ""

    def as_dict(self) -> dict:
        return {
            "use_skill": self.use_skill,
            "use_rag": self.use_rag,
            "use_memory": self.use_memory,
            "use_validator": self.use_validator,
            "selected_validators": list(self.selected_validators),
            "rationale": self.rationale,
        }


# ──────────────────────────────────────────────────────────────────────
#  Module outputs (consumed by PromptComposer)
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ModuleOutput:
    """A piece of context emitted by skill / RAG / memory / validator.

    ``relevance`` and ``confidence`` are 0-1 floats. ``risk_flags`` are
    free-form strings the optimizer can use for risk-aware ranking
    (e.g. ``"contradicts_story"``, ``"playbook_overreach"``).
    """

    module_name: str
    content: str
    confidence: float = 0.0
    relevance: float = 0.0
    risk_flags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "module_name": self.module_name,
            "content": self.content,
            "confidence": self.confidence,
            "relevance": self.relevance,
            "risk_flags": list(self.risk_flags),
            "metadata": dict(self.metadata),
        }


# ──────────────────────────────────────────────────────────────────────
#  Optimizer target abstraction
# ──────────────────────────────────────────────────────────────────────

class OptimizerTarget(ABC):
    """An optimizer target = "what we are tuning".

    Subclasses describe one optimization surface (route+gate, prompt
    compose, RAG policy, memory policy, validator policy, …). Each
    target exposes:

    * ``name`` — slot key in the policy bundle
    * ``load_policy`` / ``dump_policy`` — YAML round-trip
    * ``apply`` — pure decision function used in demos and evaluation
    """

    name: str = "abstract_target"

    @abstractmethod
    def load_policy(self, path: str) -> Any:
        """Load a policy from a YAML/JSON file."""

    @abstractmethod
    def dump_policy(self, policy: Any, path: str) -> None:
        """Write a policy to disk."""

    @abstractmethod
    def apply(self, policy: Any, **kwargs: Any) -> Any:
        """Apply the policy to a single sample. Pure function."""


# ──────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────

def coerce_route_decision(value: Any) -> RouteDecision:
    """Lossy coercion from dict / runtime-RouteDecision-like object."""
    if isinstance(value, RouteDecision):
        return value
    if isinstance(value, dict):
        return RouteDecision(
            skill_id=value.get("skill_id"),
            scene_tag=value.get("scene_tag"),
            reasoning_type=value.get("reasoning_type"),
            confidence=float(value.get("confidence", 0.0)),
            raw=dict(value.get("raw", {})),
        )
    # Duck-typing: anything with a .skill_id attribute
    return RouteDecision(
        skill_id=getattr(value, "skill_id", None),
        scene_tag=getattr(value, "scene_tag", None),
        reasoning_type=getattr(value, "reasoning_type", None),
        confidence=float(getattr(value, "confidence", 0.0)),
        raw=dict(getattr(value, "raw", {}) or {}),
    )


def coerce_module_outputs(values: Iterable[Any]) -> list[ModuleOutput]:
    out: list[ModuleOutput] = []
    for v in values:
        if isinstance(v, ModuleOutput):
            out.append(v)
        elif isinstance(v, dict):
            out.append(
                ModuleOutput(
                    module_name=v.get("module_name", "unknown"),
                    content=v.get("content", ""),
                    confidence=float(v.get("confidence", 0.0)),
                    relevance=float(v.get("relevance", 0.0)),
                    risk_flags=list(v.get("risk_flags", []) or []),
                    metadata=dict(v.get("metadata", {}) or {}),
                )
            )
    return out
