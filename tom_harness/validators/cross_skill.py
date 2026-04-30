"""CrossSkillValidator — task-scoped majority vote across sibling skills.

For tasks where multiple sibling skills hit ~the same accuracy on small
samples (e.g. Faux-pas: cs1_skill1/2/4/5/10 all 80% on 160), single-best
selection is statistically meaningless tie-break. Voting across them
catches errors that aren't shared.

Mechanism:
  - Configured with task -> [primary_skill_id, sibling_skill_id, ...]
  - At validate time: re-run each sibling skill (fresh LLM call), collect
    letter votes
  - If primary's `current_answer` is in the majority, approve
  - Else: substitute the majority-vote letter (or abstain on tie)

Cost: ~K extra LLM calls per sample where K = len(siblings). Only fires
on the configured tasks, so cost is bounded.
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field

from ..llm import LLMClient
from ..tools.skills import SkillLib
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)


SYSTEM_RAW = (
    "You are a reading comprehension assistant. Read the story and answer "
    'the multiple-choice question. Reply with ONLY a JSON object: '
    '{"answer": "A" | "B" | "C" | "D"}'
)
_LETTER_RE = re.compile(r'"answer"\s*:\s*"([A-D])"')


def _parse_letter(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text or "").strip()
    try:
        d = json.loads(text)
        a = str(d.get("answer", "")).strip().upper()
        if a in {"A","B","C","D"}: return a
    except Exception: pass
    m = _LETTER_RE.search(text)
    return m.group(1).upper() if m else ""


def _build_user_with_skill(*, story, question, options, skill_body):
    opts = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    return (
        f"## Reasoning Skill (apply before answering)\n{skill_body}\n\n"
        f"## Story\n{story}\n\n"
        f"## Question\n{question}\n\n"
        f"## Options\n{opts}\n\n"
        '## Answer\nAfter applying the skill above, reply with ONLY a JSON object: {"answer": "A"|"B"|"C"|"D"}'
    )


# Default sibling map: task_type -> [siblings to consult, NOT including primary]
# Selected per topic-relevance + 160-matrix accuracy. Primary is whatever the
# router picked; these are the *additional* voices.
DEFAULT_SIBLINGS: dict[str, list[str]] = {
    # Faux-pas: cs1_skill1 (FP-01 remark) + cs1_skill5 (FP-family) topically
    # complement primary cs1_skill2 (FP-02 knowledge). 2026-04-30 measurement
    # on full 560 samples: net +0.89pp with conservative unanimous rule.
    "Faux-pas Recognition Test":  ["cs1_skill1", "cs1_skill5"],
    # FB intentionally omitted: siblings cs1_skill3/4 share systematic bias
    # with primary cs1_skill12. Naive voting hurt -1.66pp (2026-04-30).
    # If you want to add FB back, you must first prove the siblings'
    # error patterns are decorrelated with primary's.
}


@dataclass
class CrossSkillValidator(Validator):
    """Cross-skill agreement check, **conservative override**.

    Behavior:
      - Run sibling skills, collect votes
      - Override primary's `current_answer` ONLY if ALL siblings unanimously
        agree on the SAME non-primary letter (and there are >= 2 sibling votes)
      - Any disagreement among siblings, or partial agreement with primary,
        keeps current_answer

    Why this rule: naive majority-voting let weak siblings drag down a
    stronger primary (FB v1 measurement: -1.84pp). Unanimous-disagree-with-
    primary is a much higher-confidence signal — when 2+ different prompts
    converge on the SAME alternative letter, it's likely real.
    """
    llm: LLMClient
    skill_lib: SkillLib
    sibling_map: dict[str, list[str]] = field(default_factory=lambda: dict(DEFAULT_SIBLINGS))
    max_tokens: int = 1024
    min_sibling_agreement: int = 2  # need at least this many siblings agreeing on alternative

    @property
    def applies_to_tasks(self) -> set[str]:  # type: ignore[override]
        return set(self.sibling_map.keys())

    def applies(self, task_type: str | None) -> bool:
        return task_type in self.sibling_map

    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None,
        current_answer: str,
    ) -> ValidationResult:
        siblings = self.sibling_map.get(task_type or "", [])
        if not siblings:
            return ValidationResult(valid=True, rationale="no siblings configured")

        votes: list[str] = []
        if current_answer in {"A","B","C","D"}:
            votes.append(current_answer)
        sibling_votes: dict[str, str] = {}
        for sid in siblings:
            rec = self.skill_lib.get(sid)
            if rec is None:
                logger.warning(f"sibling {sid} not in SkillLib; skipping")
                continue
            user = _build_user_with_skill(
                story=story, question=question, options=options, skill_body=rec.body,
            )
            try:
                text = self.llm.chat(SYSTEM_RAW, user, max_tokens=self.max_tokens)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"sibling {sid} LLM call failed: {e}")
                continue
            ans = _parse_letter(text)
            if ans:
                votes.append(ans)
                sibling_votes[sid] = ans

        # Conservative rule: override iff ALL siblings agree on the same
        # non-primary letter, with >= min_sibling_agreement votes.
        sibling_letters = list(sibling_votes.values())
        if len(sibling_letters) < self.min_sibling_agreement:
            return ValidationResult(valid=True,
                rationale=f"too few sibling votes ({len(sibling_letters)} < "
                          f"{self.min_sibling_agreement}); keeping {current_answer}")

        sibling_tally = Counter(sibling_letters)
        if len(sibling_tally) > 1:
            # siblings disagree among themselves — low confidence, keep primary
            return ValidationResult(valid=True,
                rationale=f"siblings split {dict(sibling_tally)}; keeping {current_answer}")

        unanimous_letter = sibling_letters[0]
        if unanimous_letter == current_answer:
            return ValidationResult(valid=True,
                rationale=f"siblings unanimous on {unanimous_letter} = primary; confirmed")

        # All siblings agree, and they disagree with primary -> override
        return ValidationResult(
            valid=False, suggested_answer=unanimous_letter,
            rationale=f"siblings {sibling_votes} unanimously {unanimous_letter} "
                      f"!= primary {current_answer}; override",
        )
