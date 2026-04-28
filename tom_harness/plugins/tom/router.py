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


# ─────────────────────────────────────────────────────────────────────────────
# v0.3d: per-ToMBench-task skill profiles.
#
# Data-driven from v0.3c's skill-correlation table (see commit message for
# diffs). Reads: "for each task, which skills had strongest +correct/-wrong
# correlation; drop the ones that hurt; keep and prioritise the ones that
# help".
#
# Lookup precedence (in select_skills):
#   1. If task_type matches a key here, use this profile verbatim.
#   2. Otherwise fall back to question_kind gating + flag boosts.
# ─────────────────────────────────────────────────────────────────────────────
TASK_PROFILES: dict[str, list[str]] = {
    # StoryModel is decisive; S06 hurt (-1), drop.
    "False Belief Task":
        ["S_build_story_model", "S_belief_query", "tpl_false_belief"],

    # Knowledge-query was net-negative (-3); evidence scorer wins big (+11).
    "Faux-pas Recognition Test":
        ["S_evidence_scorer", "S06_implicit_knowledge", "tpl_knowledge_gate"],

    # Perfect 100% with S07 + evidence_scorer; keep both.
    "Hinting Task Test":
        ["S_evidence_scorer", "S07_causal_chain"],

    # S_evidence_scorer strongest (+16); S07 supports (+7).
    "Strange Story Task":
        ["S_evidence_scorer", "S07_causal_chain"],

    # S05 v2 (story-emotion guard) is now strongly positive (+16).
    "Unexpected Outcome Test":
        ["S05_emotion_moderation", "S_evidence_scorer"],

    # S05 hurt here (-3), S_build_story_model also hurt (-2). Evidence wins.
    "Ambiguous Story Task":
        ["S_evidence_scorer", "S01_evidence_ground"],

    # S02 is the only tool that works here. Leave clean.
    "Scalar Implicature Test":
        ["S02_quantifier_solve"],

    # S04 net-neutral (dominant but ceiling=45%). Add evidence as a voting
    # peer so the finalize short-circuit has a chance to escape S04's
    # systematic biases on emotional-appeal cases.
    "Persuasion Story Task":
        ["S04_minimal_intervention", "S_evidence_scorer"],
}


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

    Lookup precedence:
      1. TASK_PROFILES[sig.task_type] if present — data-driven per-ToMBench
         task profile (v0.3d).
      2. Else fall back to SKILL_GATING by sig.question_kind.
    In both cases SIGNATURE_BOOSTS augment the selection based on flags
    (2nd-order, knowledge_gap, quantifier, hidden_emotion, persuasion).

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
    profile = TASK_PROFILES.get(sig.task_type)
    profile_is_authoritative = profile is not None
    if profile is not None:
        want: list[str] = list(profile)
    else:
        want = list(SKILL_GATING.get(sig.question_kind, []))
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
    # Fallback only when the question_kind path was used (not task profiles).
    # Task profiles are curated and authoritative — don't dilute them.
    if not profile_is_authoritative and len(out) < 2:
        for fallback in ("S_evidence_scorer", "S01_evidence_ground"):
            if fallback in available_skill_ids and fallback not in seen:
                out.append(fallback); seen.add(fallback)
    return out
