"""Signature-based skill routing.

Problem in v0.2: Planner saw every registered skill on every task and
over-invoked the generic ones (S03 fired on 71% of samples, hurting the
four tasks that didn't need subject disambiguation).

Fix: before planning, compute the TaskSignature (see memory_index) and
use it to *gate* the skill list shown to the Planner. The Planner only
sees skills that are relevant to this specific signature.

This is what SkillNet's skill-relation-graph does at scale; we do it
with a small hand-authored mapping since our skill library is tiny.
"""

from __future__ import annotations

from .memory_index import TaskSignature


# question_kind → list of skill_ids that apply
SKILL_GATING: dict[str, list[str]] = {
    "belief":      ["S_build_story_model", "S_belief_query",
                    "tpl_false_belief"],
    "knowledge":   ["S_build_story_model", "S_knowledge_query",
                    "S06_implicit_knowledge", "tpl_knowledge_gate"],
    "quantity":    ["S02_quantifier_solve"],
    "persuasion":  ["S04_minimal_intervention", "tpl_aware_of_reader"],
    "emotion":     ["S_evidence_scorer", "S05_emotion_moderation"],
    "intention":   ["S_evidence_scorer", "S07_causal_chain"],
    "action":      ["S_evidence_scorer", "S07_causal_chain"],
    "unknown":     ["S_evidence_scorer"],
}

# Additional flag-based boosts — these augment the question_kind list
SIGNATURE_BOOSTS: list[tuple[str, list[str]]] = [
    # (signature_attr_name, skill_ids to add when the flag is True)
    ("is_second_order",         ["S_build_story_model", "S_belief_query"]),
    ("has_knowledge_gap",       ["S06_implicit_knowledge", "tpl_knowledge_gate"]),
    ("has_belief_switch",       ["S_build_story_model", "S_belief_query"]),
    ("has_quantifier",          ["S02_quantifier_solve"]),
    ("has_hidden_emotion_cue",  ["S05_emotion_moderation"]),
    ("has_persuasion_intent",   ["S04_minimal_intervention"]),
]


def select_skills(sig: TaskSignature, available_skill_ids: set[str]) -> list[str]:
    """Return the filtered list of skill_ids to expose to the Planner.

    Parameters
    ----------
    sig : TaskSignature
        The pre-computed fingerprint of the current task.
    available_skill_ids : set[str]
        All skill_ids actually loaded in the skill library.

    Returns
    -------
    list[str] — deduplicated, preserves rough priority order.
    """
    want: list[str] = list(SKILL_GATING.get(sig.question_kind, []))
    for attr, extra in SIGNATURE_BOOSTS:
        if getattr(sig, attr, False):
            want.extend(extra)
    # dedup while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for s in want:
        if s in available_skill_ids and s not in seen:
            out.append(s)
            seen.add(s)
    # Always allow these generic-purpose skills as last-resort — but only
    # if the gating produced fewer than 2 suggestions (defensive).
    if len(out) < 2:
        for fallback in ("S_evidence_scorer", "S01_evidence_ground"):
            if fallback in available_skill_ids and fallback not in seen:
                out.append(fallback); seen.add(fallback)
    return out
