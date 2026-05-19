"""Route + Module-Gate optimizer target.

This target tunes Phase 1 (UNDERSTAND) and Phase 2 (GATHER):

    EnhancedRouter -> RouteDecision
    Skill / RAG / Memory / Validator gates -> ModuleGateDecision

The policy is a YAML mapping. Per scene-tag (e.g. ``false_belief``,
``faux_pas``, ``scalar_implicature``, ``ambiguous_social_cue``) it
specifies whether each module is enabled, conditionally enabled, or
disabled, plus a list of validators.

Three keywords govern each module slot:

    true         — always enable
    false        — always disable
    "conditional" — enable only when the matching ``*_condition``
                    keyword is satisfied by the task

Skill policies additionally support ``positive_triggers`` /
``negative_triggers`` text-keyword lists, ``fallback_skill``, and
``confidence_threshold`` — these together form the optimizer's
override on top of the runtime router's raw scores.

The engine is *pure*: identical inputs always produce identical
outputs. No LLM calls, no I/O after policy load.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..config import dump_yaml, load_yaml
from ..interfaces import (
    ModuleGateDecision,
    OptimizerTarget,
    RouteDecision,
    coerce_route_decision,
)


_DEFAULT_SCENE = "default"


@dataclass
class RouteGatePolicyEngine(OptimizerTarget):
    """Apply a route-gate policy to a (route_decision, task) pair.

    The engine is constructed from a parsed policy dict. Use
    :meth:`from_yaml` for the common case.
    """

    policy: dict
    name: str = "route_gate_policy"

    # ── factories ─────────────────────────────────────────────────────
    @classmethod
    def from_yaml(cls, path: str | Path) -> "RouteGatePolicyEngine":
        raw = load_yaml(path) or {}
        if "route_gate_policy" in raw and isinstance(raw["route_gate_policy"], dict):
            policy = raw["route_gate_policy"]
        else:
            policy = raw
        return cls(policy=policy)

    @classmethod
    def from_policy(cls, policy: dict) -> "RouteGatePolicyEngine":
        return cls(policy=policy or {})

    # ── OptimizerTarget interface ─────────────────────────────────────
    def load_policy(self, path: str) -> dict:
        return RouteGatePolicyEngine.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"route_gate_policy": policy}, path)

    def apply(  # type: ignore[override]
        self,
        policy: dict | None = None,
        *,
        route_decision: Any = None,
        task_text: str = "",
        options: dict[str, str] | None = None,
        **_: Any,
    ) -> ModuleGateDecision:
        if policy is None:
            policy = self.policy
        return _decide(policy, coerce_route_decision(route_decision), task_text)

    # ── convenience wrapper used by demos ─────────────────────────────
    def decide(
        self,
        route_decision: Any,
        task_text: str = "",
        options: dict[str, str] | None = None,
    ) -> ModuleGateDecision:
        return self.apply(
            route_decision=route_decision, task_text=task_text, options=options
        )

    # ── validation ────────────────────────────────────────────────────
    def validate(self) -> list[str]:
        issues: list[str] = []
        if not isinstance(self.policy, dict):
            return ["route_gate_policy must be a mapping"]
        for scene_key, scene in self.policy.items():
            if scene_key in ("skill_policies",):
                continue
            if not isinstance(scene, dict):
                issues.append(f"scene {scene_key!r} must be a mapping")
                continue
            for slot in ("skill", "rag", "memory"):
                if slot in scene and scene[slot] not in (True, False, "conditional"):
                    issues.append(
                        f"{scene_key}.{slot} must be true|false|'conditional'"
                    )
        sp = self.policy.get("skill_policies")
        if sp is not None and not isinstance(sp, dict):
            issues.append("skill_policies must be a mapping")
        return issues


# ──────────────────────────────────────────────────────────────────────
#  Decision logic
# ──────────────────────────────────────────────────────────────────────

def _decide(
    policy: dict, route: RouteDecision, task_text: str
) -> ModuleGateDecision:
    scene_key = (route.scene_tag or "").strip()
    scene_policy = _lookup_scene(policy, scene_key)
    skill_pol = _skill_policy_for(policy, route.skill_id) if route.skill_id else None

    rationale_parts: list[str] = []
    rationale_parts.append(
        f"scene={scene_key or _DEFAULT_SCENE} skill={route.skill_id} "
        f"conf={route.confidence:.2f}"
    )

    # ── skill gate ────────────────────────────────────────────────────
    use_skill, why_skill = _evaluate_skill_gate(
        scene_policy, skill_pol, route, task_text
    )
    rationale_parts.append(f"skill={'on' if use_skill else 'off'} ({why_skill})")

    # ── rag gate ──────────────────────────────────────────────────────
    use_rag, why_rag = _evaluate_module_gate(
        scene_policy, "rag", task_text, scene_policy.get("rag_condition")
    )
    rationale_parts.append(f"rag={'on' if use_rag else 'off'} ({why_rag})")

    # ── memory gate ───────────────────────────────────────────────────
    use_memory, why_mem = _evaluate_module_gate(
        scene_policy, "memory", task_text, scene_policy.get("memory_condition")
    )
    rationale_parts.append(f"memory={'on' if use_memory else 'off'} ({why_mem})")

    # ── validators ────────────────────────────────────────────────────
    validators = list(scene_policy.get("validators") or [])
    use_validator = bool(validators)

    return ModuleGateDecision(
        use_skill=use_skill,
        use_rag=use_rag,
        use_memory=use_memory,
        use_validator=use_validator,
        selected_validators=validators,
        rationale=" | ".join(rationale_parts),
    )


def _lookup_scene(policy: dict, scene_key: str) -> dict:
    if scene_key and isinstance(policy.get(scene_key), dict):
        return policy[scene_key]
    if isinstance(policy.get(_DEFAULT_SCENE), dict):
        return policy[_DEFAULT_SCENE]
    return {}


def _skill_policy_for(policy: dict, skill_id: str) -> dict | None:
    sp = policy.get("skill_policies") or {}
    if isinstance(sp, dict) and skill_id in sp and isinstance(sp[skill_id], dict):
        return sp[skill_id]
    return None


def _evaluate_skill_gate(
    scene_policy: dict,
    skill_pol: dict | None,
    route: RouteDecision,
    task_text: str,
) -> tuple[bool, str]:
    """Decide whether to apply the chosen skill on this sample.

    Order of checks (first match wins):

      1. scene_policy.skill == False  → off
      2. negative trigger fires       → off (skill misroute)
      3. confidence < threshold       → off (fallback)
      4. positive trigger fires       → on
      5. scene_policy.skill == True   → on
      6. scene_policy.skill == cond.  → on iff confidence >= threshold
    """
    # 1.
    skill_setting = scene_policy.get("skill", "conditional")
    if skill_setting is False:
        return False, "scene disables skill"

    text = (task_text or "").lower()

    # 2.
    if skill_pol:
        for trig in skill_pol.get("negative_triggers", []) or []:
            if _trigger_matches(text, trig):
                return False, f"negative trigger: {trig!r}"

    # 3.
    threshold = float(skill_pol.get("confidence_threshold", 0.0)) if skill_pol else 0.0
    if route.confidence and route.confidence < threshold:
        return False, f"confidence {route.confidence:.2f} < {threshold:.2f}"

    # 4.
    if skill_pol:
        for trig in skill_pol.get("positive_triggers", []) or []:
            if _trigger_matches(text, trig):
                return True, f"positive trigger: {trig!r}"

    # 5 / 6.
    if skill_setting is True:
        return True, "scene enables skill"
    if skill_setting == "conditional":
        return (
            route.confidence >= threshold,
            f"conditional, conf={route.confidence:.2f} thr={threshold:.2f}",
        )
    return False, f"unknown skill setting {skill_setting!r}"


def _evaluate_module_gate(
    scene_policy: dict,
    slot: str,
    task_text: str,
    condition: str | None,
) -> tuple[bool, str]:
    setting = scene_policy.get(slot, False)
    if setting is True:
        return True, f"{slot} forced on"
    if setting is False:
        return False, f"{slot} disabled"
    if setting == "conditional":
        if not condition:
            return False, f"{slot} conditional but no rule"
        if _condition_matches(task_text or "", condition):
            return True, f"{slot} cond {condition!r} matched"
        return False, f"{slot} cond {condition!r} not matched"
    return False, f"{slot} unknown setting {setting!r}"


def _trigger_matches(text: str, trigger: str) -> bool:
    """Loose token-overlap match — every whitespace-separated token in
    ``trigger`` must appear as a substring of ``text``.

    This is intentionally simple. Production code can swap in an
    embedding-based judge here without changing the policy schema.
    """
    if not trigger:
        return False
    parts = [p.strip().lower() for p in re.split(r"\s+\+\s+|\s+", trigger) if p.strip()]
    if not parts:
        return False
    text_low = text.lower()
    return all(p in text_low for p in parts)


def _condition_matches(text: str, condition: str) -> bool:
    """Conditions are short keywords like ``needs_social_norm``.

    We treat them as: "does this keyword appear, with underscores
    optionally replaced by spaces, anywhere in the task text?". Plus
    a small built-in alias map for the conditions our default policy
    uses.
    """
    text_low = text.lower()
    aliases = _CONDITION_ALIASES.get(condition, ())
    candidates: Iterable[str] = (condition.replace("_", " "), condition, *aliases)
    return any(c.lower() in text_low for c in candidates if c)


_CONDITION_ALIASES: dict[str, tuple[str, ...]] = {
    "needs_social_norm": (
        "polite",
        "rude",
        "norm",
        "etiquette",
        "appropriate",
        "should",
        "supposed to",
    ),
}
