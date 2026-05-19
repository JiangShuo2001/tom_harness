"""TODO — Validator / Finalizer / Recovery optimizer target.

Defines the abstract ``ValidatorPolicy`` interface plus stub
implementations for the eight ToM-specific validators we want to
evolve. Real validation logic is left for v0.2 — this module exists
so policy YAML can already reference these names without crashing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import dump_yaml, load_yaml
from ..interfaces import OptimizerTarget


# Validator name registry. The runtime can look up these names to
# instantiate the matching real validator class. Keeping it as a
# string-keyed registry means the optimizer never imports them
# directly — preserving the non-invasive contract.
KNOWN_VALIDATORS: tuple[str, ...] = (
    "belief_state_checker",
    "actor_observer_checker",
    "anti_overmentalizing_checker",
    "module_conflict_checker",
    "direct_answer_retention_checker",
    "draft_challenger_verifier",
    "speaker_listener_awareness_checker",
    "scalar_consistency_checker",
)


_TODO_DOC = """\
TODO ValidatorPolicy:

  select_validators(route_decision, module_outputs, task) -> list[str]
    Returns the *ordered* list of validator names to run for this
    sample. Defaults to scene_policy.validators from route_gate_policy
    when no override is given.

  run_validators(draft_answer, task, context) -> ValidatorReport
    For each selected validator, invoke the real implementation
    (looked up by name in the runtime). Aggregate flags such as:
      - whose_belief_mismatch
      - actor_observer_swap
      - over_mentalized
      - module_evidence_insufficient
      - rag_overrides_story
      - playbook_overreach
    and emit a single recommended action: keep / substitute /
    retry-with-feedback.

  The optimizer's job here is to *learn*:
    1. Which validator stack maximises repair_count and minimises
       damage_count per scene_tag.
    2. When to soft-flag (retry) vs hard-substitute the answer.
    3. Confidence thresholds for each validator's veto.
"""


@dataclass
class ValidatorPolicy(OptimizerTarget):
    policy: dict = field(default_factory=dict)
    name: str = "validator_policy"

    # ── factories ─────────────────────────────────────────────────────
    @classmethod
    def from_yaml(cls, path: str | Path) -> "ValidatorPolicy":
        raw = load_yaml(path) or {}
        return cls(policy=raw.get("validator_policy", raw) or {})

    def load_policy(self, path: str) -> dict:
        return ValidatorPolicy.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"validator_policy": policy}, path)

    # ── interface (TODO) ──────────────────────────────────────────────
    def select_validators(
        self,
        route_decision: Any,
        module_outputs: list[Any],
        task: dict,
    ) -> list[str]:
        """Return the validator names to run. Default: empty.

        v0.1 implementation: read ``self.policy["per_scene"][scene]
        .validators`` if present, else fall back to ``self.policy
        ["default"].validators``. No actual validator execution.
        """
        scene = (
            getattr(route_decision, "scene_tag", None)
            or (route_decision or {}).get("scene_tag")
            if isinstance(route_decision, dict)
            else getattr(route_decision, "scene_tag", None)
        )
        per_scene = (self.policy.get("per_scene") or {}).get(scene or "")
        if isinstance(per_scene, dict) and isinstance(
            per_scene.get("validators"), list
        ):
            return [v for v in per_scene["validators"] if v in KNOWN_VALIDATORS]
        default = self.policy.get("default") or {}
        if isinstance(default.get("validators"), list):
            return [v for v in default["validators"] if v in KNOWN_VALIDATORS]
        return []

    def run_validators(
        self,
        draft_answer: str,
        task: dict,
        context: dict,
    ) -> Any:
        raise NotImplementedError(_TODO_DOC)

    # ── OptimizerTarget ───────────────────────────────────────────────
    def apply(self, policy: dict | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError(_TODO_DOC)

    # ── validation ────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        issues: list[str] = []
        per_scene = self.policy.get("per_scene")
        if per_scene is not None and not isinstance(per_scene, dict):
            issues.append("per_scene must be a mapping")
        for k, block in (per_scene or {}).items():
            vs = (block or {}).get("validators") or []
            for v in vs:
                if v not in KNOWN_VALIDATORS:
                    issues.append(
                        f"per_scene.{k} references unknown validator {v!r}"
                    )
        return issues
