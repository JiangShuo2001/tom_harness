"""PolicyBundle — the unified output of the Harness Optimizer.

A bundle aggregates per-target policies (route+gate, prompt-compose,
RAG, memory, validator) and metadata into a single YAML file the
runtime can consume. Two design points:

1. *Sparse*: missing slots are allowed and mean "use built-in default".
2. *Mergeable*: ``merge`` returns a new bundle preferring the right-hand
   side's non-empty slots — useful when stacking a search-output bundle
   on top of the defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import dump_yaml, load_yaml


_KNOWN_SLOTS = (
    "route_gate_policy",
    "prompt_compose_policy",
    "rag_policy",
    "memory_policy",
    "validator_policy",
)


@dataclass
class PolicyBundle:
    """In-memory container for one optimizer artefact."""

    version: str = "0.1.0"
    created_at: str = ""
    description: str = "Non-invasive policy bundle for HarnessRuntime v3"

    route_gate_policy: dict | None = None
    prompt_compose_policy: dict | None = None
    rag_policy: dict | None = None
    memory_policy: dict | None = None
    validator_policy: dict | None = None

    metadata: dict = field(default_factory=dict)

    # ── construction / round-trip ─────────────────────────────────────
    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyBundle":
        raw = load_yaml(path) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"PolicyBundle YAML must be a mapping, got {type(raw)}")
        bundle = cls(
            version=str(raw.get("version", "0.1.0")),
            created_at=str(raw.get("created_at") or ""),
            description=str(raw.get("description") or ""),
            metadata=dict(raw.get("metadata") or {}),
        )
        for slot in _KNOWN_SLOTS:
            setattr(bundle, slot, raw.get(slot) or None)
        return bundle

    def to_yaml(self, path: str | Path) -> None:
        dump_yaml(self.as_dict(), path)

    def as_dict(self) -> dict:
        out: dict = {
            "version": self.version,
            "created_at": self.created_at or _now_iso(),
            "description": self.description,
        }
        for slot in _KNOWN_SLOTS:
            out[slot] = getattr(self, slot)
        out["metadata"] = self.metadata
        return out

    # ── algebra ───────────────────────────────────────────────────────
    def merge(self, other: "PolicyBundle") -> "PolicyBundle":
        """Return a new bundle: ``self`` overlaid with ``other``'s non-null slots.

        Metadata is shallow-merged; per-slot dicts are *replaced* wholesale
        when the rhs is non-null. We intentionally avoid deep-merge here
        — policies are easier to reason about when each slot is owned by
        exactly one bundle in the stack.
        """
        merged = PolicyBundle(
            version=other.version or self.version,
            created_at=_now_iso(),
            description=other.description or self.description,
            metadata={**self.metadata, **other.metadata},
        )
        for slot in _KNOWN_SLOTS:
            rhs = getattr(other, slot)
            setattr(merged, slot, rhs if rhs is not None else getattr(self, slot))
        return merged

    # ── validation ────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        """Return a list of human-readable issues (empty list = OK).

        Validation here is intentionally lightweight — it sanity-checks
        structure rather than semantics. Each target has its own deeper
        validator (e.g. ``RouteGatePolicyEngine.validate``).
        """
        issues: list[str] = []
        if not self.version:
            issues.append("missing version")
        for slot in _KNOWN_SLOTS:
            v = getattr(self, slot)
            if v is None:
                continue
            if not isinstance(v, dict):
                issues.append(f"slot {slot!r} must be a mapping or null")
        if self.metadata is not None and not isinstance(self.metadata, dict):
            issues.append("metadata must be a mapping")
        return issues


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
