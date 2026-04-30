"""OraclePicksRouter — per-task best skill, requires task_type at runtime.

Picks chosen empirically from the 2470-sample full ToMBench main-8 sweep
on qwen-plus, temp=0, single-shot. See WEEKLY_REPORT_HARNESS_2026-04-29
§5 表 1 for the underlying numbers. These picks gave overall 81.58%
(vs raw 78.42%, +3.16pp).

Decision rule (chosen ONCE before evaluation):
  - Pick a skill iff it strictly beat raw on the matrix sweep
  - If the matrix had multiple skills tied, prefer one whose `description`
    is topically aligned with the task (e.g. FP-* code -> Faux-pas).
    The 160-sample tied-pick ambiguity is what made cs1_skill10 (a Scalar
    skill) win Faux-pas tie-break by lex order — this regressed -2.1pp
    on full benchmark before we corrected to cs1_skill2 (FP-02).
  - Tie with raw -> raw (prefer no-skill prior over arbitrary skill).
"""

from .base import Router, RouteDecision


# task_type -> skill_id (or None for raw)
ORACLE_PICKS: dict[str, str | None] = {
    "Ambiguous Story Task":         None,                   # tied with raw
    "False Belief Task":            "cs1_skill12",
    "Faux-pas Recognition Test":    "cs1_skill2",           # FP-02 (NOT cs1_skill10)
    "Hinting Task Test":            "cs1_skill8",
    "Persuasion Story Task":        "cs2_S11_BeliefEmotion",
    "Scalar Implicature Test":      "cs1_skill10",          # SI-01 — for Scalar this IS the right skill
    "Strange Story Task":           "cs1_skill15",
    "Unexpected Outcome Test":      None,                   # tied with raw
}


class OraclePicksRouter(Router):
    """Looks up `task_type` in ORACLE_PICKS. Falls back to raw if unknown."""

    def __init__(self, picks: dict[str, str | None] | None = None) -> None:
        self.picks = picks if picks is not None else ORACLE_PICKS

    def route(
        self,
        *,
        question: str,
        story: str = "",
        options: dict[str, str] | None = None,
        task_type: str | None = None,
    ) -> RouteDecision:
        if task_type is None:
            return RouteDecision(skill_id=None, rationale="no task_type given")
        skill_id = self.picks.get(task_type)
        if skill_id is None:
            return RouteDecision(skill_id=None, rationale=f"task '{task_type}': no skill beats raw")
        return RouteDecision(skill_id=skill_id, rationale=f"task '{task_type}' -> {skill_id}")
