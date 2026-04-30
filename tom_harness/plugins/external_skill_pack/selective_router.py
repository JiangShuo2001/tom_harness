"""SelectiveRouter — chooses one of {raw, set1, set2} per case.

Frozen routing rules from v0.4-selective-baseline-beaten:
  - has_quantifier + "how many" question  → set1_direct  (Scalar)
  - has_belief_switch + belief query      → set1_direct  (False Belief)
  - "should X but / surprising"           → set2_direct  (Unexpected)
  - everything else                        → raw          (no skill)

This is the SkillPackAdapter that wraps both set1 and set2 and routes
between them (or to no-skill / "raw"). It uses extract_signature flags
plus a few targeted regex; no LLM router involved at this layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..tom.memory_index import extract_signature
from ...tools.skills import SkillLib
from .adapter import RoutingResult, SkillPackAdapter, SkillPackInfo
from .set1_adapter import Set1Adapter
from .set2_adapter import Set2Adapter


_QUANTITY_Q = re.compile(r"\bhow many\b|几|多少", re.IGNORECASE)
_BELIEF_Q = re.compile(
    r"\bwhere\s+(?:will|does|did)\b|"
    r"\bexpect\s+to\s+find\b|"
    r"\bwill\s+\w+\s+find\b|"
    r"\b(?:thinks|believes)\s+(?:is|are)\s+in\b|"
    r"去哪里|在哪里|认为.*在|以为.*是",
    re.IGNORECASE,
)
_UNEXPECTED_CUE = re.compile(
    r"\bshould\s+(?:feel|be|show)[^.!?]*\bbut\b|"
    r"\bexpected to[^.!?]*\bbut\b|"
    r"\bsurprising\b|"
    r"应该.*但是?|本应.*却",
    re.IGNORECASE,
)


@dataclass
class SelectiveRouter(SkillPackAdapter):
    """Routes between set1 and set2 (or NONE/raw) using v0.4 rules."""

    pack_root: Any = None             # not used; kept for API uniformity
    routing_mode: str = "v04_selective"

    set1: Set1Adapter = field(default_factory=Set1Adapter, init=False)
    set2: Set2Adapter = field(
        default_factory=lambda: Set2Adapter(routing_mode="signature"),
        init=False,
    )

    def load_into(self, skill_lib: SkillLib) -> int:
        n = 0
        n += self.set1.load_into(skill_lib)
        n += self.set2.load_into(skill_lib)
        return n

    def route(
        self, *, question: str, story: str = "",
        options: dict[str, str] | None = None, task_type: str | None = None,
    ) -> RoutingResult:
        sig = extract_signature(question=question, story=story,
                                task_type=task_type or "", options=options)
        q = question or ""
        ctx = f"{q} {story or ''}"

        # Rule 1 — Scalar (always pick set1's prior- or posterior-estimation skill)
        if sig.has_quantifier and _QUANTITY_Q.search(q):
            # posterior if observation present
            qs = f"{q} {story}".lower()
            posterior = ("after" in qs or "数过" in qs or "数完" in qs) and \
                        bool(re.search(r"\b\d+\s+(?:are|is|wear|of|个|只|盘)\b", qs))
            sid = "cs1_skill11" if posterior else "cs1_skill10"
            return RoutingResult(skill_id=sid, confidence=0.9,
                                 rationale=f"v0.4 selective → set1 ({sid}): scalar")

        # Rule 2 — False Belief (forced to set1's first-order belief skill)
        if sig.has_belief_switch and _BELIEF_Q.search(q):
            return RoutingResult(skill_id="cs1_skill3", confidence=0.9,
                                 rationale="v0.4 selective → cs1_skill3: 1st-order belief")

        # Rule 3 — Unexpected Outcome
        if _UNEXPECTED_CUE.search(ctx):
            return RoutingResult(skill_id="cs2_S5_Expectation", confidence=0.85,
                                 rationale="v0.4 selective → cs2_S5_Expectation: unexp")

        # Rule 4 — fallthrough: raw
        return RoutingResult(skill_id=None, confidence=0.7,
                             rationale="v0.4 selective: no skill cue → raw")

    def metadata(self) -> SkillPackInfo:
        info1 = self.set1.metadata()
        info2 = self.set2.metadata()
        return SkillPackInfo(
            pack_name="selective_v04",
            contributor="harness/JiangShuo2001",
            pack_version="v0.4-selective-baseline-beaten",
            n_skills=info1.n_skills + info2.n_skills,
            skill_ids=info1.skill_ids + info2.skill_ids,
            routing_mode=self.routing_mode,
            extras={"set1": info1.extras, "set2": info2.extras},
        )
