"""TODO — RAG / Memory / Skill internal-policy optimizer targets.

These targets are *not* fully implemented in v0.1. They define the
intended interface so future work can plug in a real evaluator /
proposer without touching the existing route+gate or prompt-compose
plumbing.

For each module we keep three concepts:

  * **Policy schema** — what YAML the search can mutate.
  * **PolicyEngine stub** — a class that loads/validates the YAML.
  * **TODO notes** — what the engine should actually *do* once wired in.

The actual ToM-runtime hookup is described in ``docs/integration_suggestions.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import dump_yaml, load_yaml
from ..interfaces import OptimizerTarget


# ──────────────────────────────────────────────────────────────────────
#  RAG
# ──────────────────────────────────────────────────────────────────────

_RAG_TODO = """\
TODO RAGPolicyEngine:

  Inputs:
    - route_decision (skill_id, scene_tag, reasoning_type, confidence)
    - task (story, question, options)
    - per-scene policy block: enabled / query_rewrite / top_k /
      require_relevance_score / source_filter / contradiction_filter
    - challenger_evidence_enabled

  Behaviour:
    1. If policy says enabled == false, return [] (skip RAG entirely).
    2. Otherwise, build a query using the `query_rewrite` template +
       relevant fields from the task (e.g. ``"{question} {scene_tag}"``).
    3. Call the existing RAG engine in retrieval-only mode; pass
       ``top_k`` and any source filters.
    4. Filter results below ``require_relevance_score``.
    5. Optional contradiction filter: drop docs whose claims directly
       contradict the story (heuristic or LLM-judge).
    6. Optional challenger retrieval: if the draft answer disagrees
       with the direct answer, retrieve evidence that *contradicts*
       the chosen option to stress-test it.
"""


@dataclass
class RagPolicyEngine(OptimizerTarget):
    policy: dict
    name: str = "rag_policy"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RagPolicyEngine":
        raw = load_yaml(path) or {}
        return cls(policy=raw.get("rag_policy", raw) or {})

    def load_policy(self, path: str) -> dict:
        return RagPolicyEngine.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"rag_policy": policy}, path)

    def apply(self, policy: dict | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError(_RAG_TODO)


# ──────────────────────────────────────────────────────────────────────
#  Memory
# ──────────────────────────────────────────────────────────────────────

_MEMORY_TODO = """\
TODO MemoryPolicyEngine:

  Each memory entry should look like:

      {
        "memory_id": "commitment_priority_arbitration",
        "strategy": "...",
        "positive_triggers": [...],
        "negative_triggers": [...],
        "known_losses": ["Completion_0002"],
        "known_wins": ["Completion_0008"]
      }

  Behaviour:
    1. Score each entry against task text using positive/negative
       triggers (same loose-overlap rule used by route_gate_target).
    2. Demote entries whose ``known_losses`` overlap with this task's
       failure cohort (skill_id / scene_tag).
    3. Keep top-K by net score; emit them as ModuleOutput(module='memory').
    4. Track which entries were used so the experience store can
       update ``known_wins`` / ``known_losses`` after evaluation.
"""


@dataclass
class MemoryPolicyEngine(OptimizerTarget):
    policy: dict
    name: str = "memory_policy"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MemoryPolicyEngine":
        raw = load_yaml(path) or {}
        return cls(policy=raw.get("memory_policy", raw) or {})

    def load_policy(self, path: str) -> dict:
        return MemoryPolicyEngine.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"memory_policy": policy}, path)

    def apply(self, policy: dict | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError(_MEMORY_TODO)


# ──────────────────────────────────────────────────────────────────────
#  Skill internals
# ──────────────────────────────────────────────────────────────────────

_SKILL_TODO = """\
TODO SkillPolicyEngine:

  Per-skill policy block:

      skill7_nonverbal_cue:
        positive_triggers: [...]
        negative_triggers: [...]
        fallback_skill: observer_perspective_inference
        confidence_threshold: 0.72
        risk_flags: [over_mentalizing, actor_observer_swap]
        known_wins: [...]
        known_losses: [...]

  Behaviour:
    1. After the runtime router returns its top-1 skill, check the
       skill's policy: do negative triggers fire? confidence below
       threshold?
    2. If yes → either drop the skill entirely or substitute
       ``fallback_skill``.
    3. Forward risk_flags into the ModuleOutput so the
       PromptComposer can downrank or soft-format.

  Note: positive_triggers / negative_triggers here OVERLAP with the
  ones in route_gate_policy.skill_policies. Recommended convention:
  scene-level triggers live in route_gate_policy; skill-deep
  metadata (risk flags, known wins/losses, fallbacks) lives here.
"""


@dataclass
class SkillPolicyEngine(OptimizerTarget):
    policy: dict
    name: str = "skill_policy"

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SkillPolicyEngine":
        raw = load_yaml(path) or {}
        return cls(policy=raw.get("skill_policy", raw) or {})

    def load_policy(self, path: str) -> dict:
        return SkillPolicyEngine.from_yaml(path).policy

    def dump_policy(self, policy: dict, path: str) -> None:
        dump_yaml({"skill_policy": policy}, path)

    def apply(self, policy: dict | None = None, **kwargs: Any) -> Any:
        raise NotImplementedError(_SKILL_TODO)
