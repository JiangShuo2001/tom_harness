"""ToM failure-type → remedy mapping.

Classifies a failed step against ToM failure taxonomy and proposes a
recovery action (usually: replan and inject the relevant skill(s)).

The taxonomy mirrors `tom_skills.json:failure_type_to_skill_mapping`.
"""

from __future__ import annotations

from ...hooks import RecoveryDirective
from ...schemas import ExecutionContext, ExecutionTrace, Step


FAILURE_TO_SKILLS: dict[str, list[str]] = {
    "knowledge_gate_bypass":    ["S01_knowledge_state_tracking", "S02_knowledge_gate_filter"],
    "false_belief_tracking":    ["S03_false_belief_tracking"],
    "second_order_belief":      ["S03_false_belief_tracking", "S04_second_order_belief"],
    "double_bluff":             ["S05_double_bluff_reasoning", "S06_pragmatic_speech_act"],
    "social_norm_violation":    ["S06_pragmatic_speech_act", "S07_audience_adaptation"],
    "quantifier_grounding":     ["S08_quantifier_grounding"],
    "hidden_emotion":           ["S09_emotion_behind_mask"],
    "perspective_taking":       ["S10_perspective_integration"],
    "desire_action_mismatch":   ["S11_desire_belief_interaction"],
    "pragmatic_inference":      ["S06_pragmatic_speech_act"],
    "surface_match_trap":       ["S01_knowledge_state_tracking", "S02_knowledge_gate_filter"],
    "intention_inference":      ["S05_double_bluff_reasoning", "S11_desire_belief_interaction"],
}


def classify_failure(step: Step, trace: ExecutionTrace, ctx: ExecutionContext) -> str:
    """Very lightweight heuristic classifier.

    Looks at the step's description, the error message, and the original
    question to pick a failure bucket. A production system would use an
    LLM-as-judge here; the heuristics are intentionally conservative so
    the scheduler's default replan path always produces *some* progress.
    """
    desc = (step.description or "").lower()
    err = (trace.observation.error if trace.observation else "") or ""
    err = err.lower()
    q = (ctx.global_context.original_question if ctx.global_context else "").lower()

    # 1) Tool-resolution failures are structural, not ToM-specific
    if "not registered" in err or "permission" in err:
        return "structural"

    # 2) Belief-reasoning cues
    if "second-order" in desc or "second order" in desc or "二阶" in desc:
        return "second_order_belief"
    if "false belief" in desc or "错误信念" in desc or "believes" in desc:
        return "false_belief_tracking"

    # 3) Knowledge-gate cues
    if "knows" in desc or "知道" in desc or "never seen" in q or "一无所知" in q:
        return "knowledge_gate_bypass"

    # 4) Pragmatic / social
    if "faux" in desc or "失言" in desc or "失当" in q:
        return "pragmatic_inference"
    if "quantifier" in desc or "most " in q or "几乎一半" in q:
        return "quantifier_grounding"

    # 5) Emotion
    if "hidden" in desc or "隐藏" in desc or "hides" in q:
        return "hidden_emotion"

    return "general"


def on_step_failure(step: Step, trace: ExecutionTrace, context: ExecutionContext) -> RecoveryDirective | None:
    """Hook callback: classify, then propose a recovery directive."""
    ftype = classify_failure(step, trace, context)
    if ftype == "structural":
        return RecoveryDirective(action="abort", failure_type=ftype,
                                 note=trace.observation.error if trace.observation else "structural error")
    remedy_skills = FAILURE_TO_SKILLS.get(ftype, [])
    return RecoveryDirective(
        action="replan",
        failure_type=ftype,
        inject_skills=remedy_skills,
        note=f"classified as {ftype}; injecting skills: {remedy_skills}",
    )
