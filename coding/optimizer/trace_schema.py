"""Trace schema for optimizer experience records.

Traces describe what happened on a single sample under a particular
policy bundle. They are the *input* to evaluators (which compute
aggregate scores and credit-assignment) and to proposers (which mutate
policies to produce the next candidate bundle).

We deliberately use plain dicts at the I/O boundary — JSON
serialisation, schema evolution, and streaming all stay simple. The
``Trace`` dataclass is a convenience helper for in-memory construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Top-level keys expected in a trace JSON record. Validators and
# evaluators consult this list to detect missing fields without
# importing the dataclass.
TRACE_KEYS: tuple[str, ...] = (
    "sample_id",
    "gold",
    "predicted",
    "direct_answer",
    "route_decision",
    "active_modules",
    "module_outputs",
    "prompt_tokens",
    "validator_flags",
    "failure_type",
    "optimizer_note",
)


# Failure-type vocabulary used by the credit-assignment evaluator.
# Add new tags here rather than free-typing strings in proposer code.
FAILURE_TYPES: tuple[str, ...] = (
    "skill_misroute",
    "skill_overtrigger",
    "rag_noise_injected",
    "memory_overreach",
    "module_conflict",
    "overmentalizing",
    "format_error",
    "validator_false_positive",
    "validator_false_negative",
    "context_overload",
    "ok",
    "unknown",
)


@dataclass
class Trace:
    """In-memory trace record. Use ``as_dict()`` for serialization."""

    sample_id: str
    gold: str = ""
    predicted: str = ""
    direct_answer: str = ""

    route_decision: dict = field(default_factory=dict)
    active_modules: list[str] = field(default_factory=list)
    module_outputs: dict[str, Any] = field(default_factory=dict)

    prompt_tokens: int = 0
    validator_flags: list[str] = field(default_factory=list)
    failure_type: str = "unknown"
    optimizer_note: str = ""

    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        out: dict = {
            "sample_id": self.sample_id,
            "gold": self.gold,
            "predicted": self.predicted,
            "direct_answer": self.direct_answer,
            "route_decision": dict(self.route_decision),
            "active_modules": list(self.active_modules),
            "module_outputs": dict(self.module_outputs),
            "prompt_tokens": int(self.prompt_tokens),
            "validator_flags": list(self.validator_flags),
            "failure_type": self.failure_type,
            "optimizer_note": self.optimizer_note,
        }
        if self.extra:
            out["extra"] = dict(self.extra)
        return out

    # ── derived ───────────────────────────────────────────────────────
    @property
    def correct(self) -> bool:
        return bool(self.gold) and self.gold == self.predicted

    @property
    def repaired(self) -> bool:
        """Direct answer was wrong, modules turned it into a win."""
        return (
            self.direct_answer != ""
            and self.direct_answer != self.gold
            and self.predicted == self.gold
        )

    @property
    def damaged(self) -> bool:
        """Direct answer was right, modules made it wrong."""
        return (
            self.direct_answer != ""
            and self.direct_answer == self.gold
            and self.predicted != self.gold
        )


def validate_trace_dict(record: dict) -> list[str]:
    """Lightweight schema check. Returns a list of missing/invalid keys."""
    issues: list[str] = []
    for k in ("sample_id", "predicted"):
        if not record.get(k):
            issues.append(f"missing required key: {k}")
    if "failure_type" in record and record["failure_type"] not in FAILURE_TYPES:
        issues.append(
            f"failure_type {record['failure_type']!r} not in vocabulary; "
            f"see FAILURE_TYPES"
        )
    if "active_modules" in record and not isinstance(
        record["active_modules"], list
    ):
        issues.append("active_modules must be a list")
    return issues
