"""ToM-aware memory enrichment — v0.2.

Design brief
------------
The naive memory store retrieves by text similarity of (question | task_type).
That is a poor predictor of plan reusability: two questions with identical
wording can need very different plans (e.g. simple false-belief vs. 2nd-order),
and two structurally identical questions can read very differently.

What actually predicts reusability is the *shape of the reasoning problem*:
  - What is being asked about (emotion, knowledge, quantity, intention, action)?
  - What linguistic markers are present (quantifiers, knowledge gaps, belief
    switches, emotion-hiding cues, persuasion intent)?
  - What structural context (character count, location count, belief order)?

This module computes a *task signature* — a small dict fingerprint — and
stores it in `Memory.metadata`. The retrieval tool already supports
`metadata_filter`, so downstream the planner can do structured pre-filtering
before semantic re-ranking.

Hooks installed (by plugins/tom/install.py):
  - enrich_memory:  fills signature fields into Memory.metadata on write
  - before_plan:    stamps signature into ContextManager.transient so
                    other plugins (and the planner prompt) can consult it

Contract with core: this file never mutates non-metadata fields of any
schema. Core code never reads these fields.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from ...schemas import Memory


# ─────────────────────────────────────────────────────────────────────────────
# Lexical cue sets — bilingual (ToMBench is EN + ZH)
# ─────────────────────────────────────────────────────────────────────────────

_QUANTIFIER_RE = re.compile(
    r"\bmost\b|\ball of\b|\bnone of\b|\balmost none\b|\balmost all\b|"
    r"\balmost half\b|\bhalf of\b|\ba few\b|\bseveral\b|\bmany\b|\bsome\b|"
    r"大多数|大部分|几乎所有|几乎没有|几乎一半|一半|少数|一些|部分|几个",
    re.IGNORECASE,
)

_KNOWLEDGE_GAP_RE = re.compile(
    r"\bnever (?:seen|heard|encountered|met)\b|\bno idea\b|\bunaware\b|"
    r"\bhas no knowledge\b|\bdoes not know\b|\bdoesn't know\b|"
    r"\bcannot see\b|\bcould not see\b|"
    r"从未见过|从未听说|一无所知|不知道|不清楚|看不见|看不到",
    re.IGNORECASE,
)

_BELIEF_SWITCH_LEAVE = re.compile(
    r"\bleaves\b|\bgoes out\b|\bwalks away\b|\bnot present\b|\babsent\b|"
    r"\bwhile .+? is (?:gone|away)\b|离开|走开|不在场|出去|不在",
    re.IGNORECASE,
)

_BELIEF_SWITCH_MOVE = re.compile(
    r"\bmoves\b|\bmoved\b|\bputs .+ into\b|\btakes .+ out\b|\bhides\b|"
    r"把.+放进|放到|藏到|移到|搬到",
    re.IGNORECASE,
)

_HIDDEN_EMOTION_RE = re.compile(
    r"\bsmiles\b|\bsmiled\b|\bpretend(?:s|ed)?\b|"
    r"\bhides? .+ (?:feelings|emotions)\b|\bforces? a smile\b|"
    r"\boutwardly .+ but\b|假装|强颜欢笑|表面上|内心却",
    re.IGNORECASE,
)

_PERSUASION_RE = re.compile(
    r"\bconvince\b|\bpersuade\b|\bhow (?:does|should)\b|"
    r"\bwants .+ to stop\b|\bwants .+ to (?:do|not)\b|"
    r"说服|劝说|希望.+不要|想要.+做|如何让",
    re.IGNORECASE,
)

_INTENTION_Q_RE = re.compile(
    r"\bwhy does\b|\bwhy did\b|"
    r"\bwhat (?:does|is) .+ (?:intend|plan|want to do)\b|"
    r"为什么|打算|意图|想做",
    re.IGNORECASE,
)

_SECOND_ORDER_Q_RE = re.compile(
    r"\bwhat does .+ think .+ (?:will|would|thinks|believes)\b|"
    r"什么.+认为.+会|什么.+以为.+会",
    re.IGNORECASE,
)

# Character-name heuristics
_EN_NAME = re.compile(r"\b([A-Z][a-z]{1,})\b")
_ZH_NAME_PATTERNS = [
    re.compile(r"([\u4e00-\u9fff]{2,3})(?=说|问|答|是|有|想|觉|认为)"),
]
_STOP_CAP = {"The", "A", "An", "It", "In", "On", "After", "Before",
             "When", "Then", "They", "He", "She", "His", "Her", "And",
             "Because", "But", "So", "That", "This", "These", "Those",
             "For", "If", "At", "By", "Of", "To", "While"}


@dataclass
class TaskSignature:
    """Compact structural fingerprint of a ToM problem."""
    task_type: str = "unknown"
    question_kind: str = "unknown"    # emotion | knowledge | quantity | persuasion | intention | action | belief
    character_count: int = 0
    belief_order: int = 0             # 0 / 1 / 2
    has_knowledge_gap: bool = False
    has_belief_switch: bool = False
    has_quantifier: bool = False
    has_hidden_emotion_cue: bool = False
    has_persuasion_intent: bool = False
    is_second_order: bool = False
    answer_letter_space: int = 4      # 2 (A/B) vs 4 (A/B/C/D)

    def as_filter(self) -> dict[str, Any]:
        """Which fields to use for structured memory pre-filtering.

        Only discriminative, high-confidence flags — noisy fields like
        `character_count` exact-match are omitted because they'd
        over-constrain retrieval.
        """
        return {
            "question_kind": self.question_kind,
            "has_knowledge_gap": self.has_knowledge_gap,
            "has_quantifier": self.has_quantifier,
            "is_second_order": self.is_second_order,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Pure extractor
# ─────────────────────────────────────────────────────────────────────────────

def extract_signature(
    *,
    question: str,
    story: str = "",
    task_type: str = "unknown",
    options: dict[str, str] | None = None,
) -> TaskSignature:
    """Compute a TaskSignature from question + story text.

    Pure function; no LLM calls, no side effects. <1ms typical — safe to
    call on every task without cost concern.
    """
    q = question or ""
    s = story or ""
    combined = f"{s}\n{q}"

    # Character union (EN capitals minus stopwords) ∪ (ZH name patterns)
    chars: set[str] = set(_EN_NAME.findall(combined)) - _STOP_CAP
    for pat in _ZH_NAME_PATTERNS:
        chars |= set(pat.findall(combined))

    is_2nd_order = bool(_SECOND_ORDER_Q_RE.search(q))
    belief_order = 2 if is_2nd_order else (1 if "belief" in task_type.lower() else 0)

    # Question-kind: coarse multi-signal classifier
    ql = q.lower()
    if any(w in ql for w in ["feel", "mood", "emotion", "情绪", "感受", "心情"]):
        question_kind = "emotion"
    elif _PERSUASION_RE.search(q):
        question_kind = "persuasion"
    elif any(w in ql for w in ["how many", "几", "多少"]):
        question_kind = "quantity"
    elif any(w in ql for w in ["know", "knows", "知道", "清楚"]):
        question_kind = "knowledge"
    elif _INTENTION_Q_RE.search(q):
        question_kind = "intention"
    elif any(w in ql for w in ["where", "find", "look", "expect", "认为", "会去"]):
        question_kind = "belief"
    elif any(w in ql for w in ["what will", "what does", "next", "接下来"]):
        question_kind = "action"
    else:
        question_kind = "unknown"

    return TaskSignature(
        task_type=task_type,
        question_kind=question_kind,
        character_count=len(chars),
        belief_order=belief_order,
        has_knowledge_gap=bool(_KNOWLEDGE_GAP_RE.search(combined)),
        has_belief_switch=bool(
            _BELIEF_SWITCH_LEAVE.search(combined)
            and _BELIEF_SWITCH_MOVE.search(combined)
        ),
        has_quantifier=bool(_QUANTIFIER_RE.search(combined)),
        has_hidden_emotion_cue=bool(_HIDDEN_EMOTION_RE.search(combined)),
        has_persuasion_intent=bool(_PERSUASION_RE.search(q)),
        is_second_order=is_2nd_order,
        answer_letter_space=(len(options) if options else 4),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Hook callbacks
# ─────────────────────────────────────────────────────────────────────────────

def enrich_memory(memory: Memory) -> Memory:
    """Populate memory.metadata with TaskSignature + skill trajectory.

    Called after a successful task by the Scheduler (hook event: enrich_memory).
    Pure function; returns a modified copy via model_copy.
    """
    sig = extract_signature(
        question=memory.task.question,
        task_type=memory.task.task_type,
    )
    skill_trajectory: list[str] = []
    for phase in memory.plan.phases:
        for step in phase.steps:
            if step.tool and step.tool.tool_type.value == "skill":
                skill_trajectory.append(
                    step.tool.tool_params.get("skill_id", step.tool.tool_name)
                )
    new_metadata: dict[str, Any] = dict(memory.metadata)
    new_metadata.update(asdict(sig))
    new_metadata["skill_trajectory"] = skill_trajectory
    new_metadata["num_phases"] = len(memory.plan.phases)
    new_metadata["plan_phase_signature"] = "|".join(
        p.phase_name.lower()[:16] for p in memory.plan.phases
    )
    return memory.model_copy(update={"metadata": new_metadata})
