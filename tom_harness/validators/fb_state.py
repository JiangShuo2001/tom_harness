"""FBStateBackedValidator — narrow procedural check on Sally-Anne-style FB.

Pragmatic, narrow scope: looks for the canonical structure
  "X puts OBJ in LOC1; X leaves; Y moves OBJ to LOC2; X comes back"
followed by "Where will X look for OBJ?"

When the structure is identifiable, the right answer should reference
LOC1 (X's last-known location) — the "false belief". If LLM picks an
option that mentions LOC2 (the actual current location) instead, flag.

This is a state-externalization validator: pure Python, no LLM. It only
fires on samples where the textual pattern is parseable; otherwise
abstains. Expected hit rate: maybe 20-40% of FB samples will match;
within those, maybe 30-50% catch a real LLM error.

Limitations (acknowledged):
  - English only (the regex set assumes English ToMBench EN)
  - Requires explicit "leaves/leaves the room/goes out" cue
  - Doesn't handle 2nd-order belief, content false belief, etc.

If the validator catches even +1pp on full FB 600, it earns its keep.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .base import Validator, ValidationResult


# Cues that the target character was absent during a state change
_ABSENT_CUES = re.compile(
    r"\b(leaves\s+the\s+room|left\s+the\s+room|goes?\s+out|went\s+out|"
    r"is\s+(?:not\s+)?in\s+the\s+room|absent|away|outside|on\s+a\s+(?:trip|holiday|"
    r"call)|in\s+another\s+room)\b",
    re.IGNORECASE,
)

# Move events. We capture the destination location only.
# Two forms:
#   "X puts/places/hides OBJ in/into/inside/onto LOC"
#   "X moves/transfers/takes OBJ [from LOC0] to LOC"
_MOVE_RE = re.compile(
    r"\b(?:moves?|moved|puts?|put|transfers?|transferred|places?|placed|"
    r"hides?|hid|takes?|took|brings?|brought|drops?|dropped)\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<obj>\w+(?:\s+\w+)?)"
    r"(?:\s+from\s+(?:the\s+|a\s+|an\s+)?\w+(?:\s+\w+)?)?"        # optional "from LOC0"
    r"\s+(?:to|into|in|inside|under|onto)\s+"
    r"(?:the\s+|a\s+|an\s+)?(?P<loc>\w+(?:\s+\w+)?)",
    re.IGNORECASE,
)

# "Where will X look for Y" pattern
_LOOK_QUESTION = re.compile(
    r"\bwhere\b.*?\b(?:will|does|did|would)\b.*?\b(?:look|search|seek)\b",
    re.IGNORECASE,
)


def _option_mentions(option_text: str, location: str) -> bool:
    """Loose check: does the option text contain the location word(s)?"""
    if not option_text or not location:
        return False
    loc_clean = location.strip().lower()
    if not loc_clean:
        return False
    return loc_clean in option_text.lower()


@dataclass
class FBStateBackedValidator(Validator):
    """Catches "false belief means LLM picked the actual current location" errors."""

    @property
    def applies_to_tasks(self) -> set[str]:  # type: ignore[override]
        return {"False Belief Task"}

    def applies(self, task_type: str | None) -> bool:
        return task_type == "False Belief Task"

    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None,
        current_answer: str,
    ) -> ValidationResult:
        # Quick gate: must be a "where will X look" question
        if not _LOOK_QUESTION.search(question or ""):
            return ValidationResult(valid=True, rationale="not a 'where will X look' question; abstaining")

        # Must contain absent-cue
        if not _ABSENT_CUES.search(story or ""):
            return ValidationResult(valid=True, rationale="no absent-character cue; abstaining")

        # Find moves: we expect (obj, loc1) then (obj, loc2) on the same object
        moves: list[tuple[str, str, int]] = []  # (obj, loc, char_pos)
        for m in _MOVE_RE.finditer(story or ""):
            obj = m.group("obj").lower().strip()
            loc = m.group("loc").lower().strip()
            moves.append((obj, loc, m.start()))

        if len(moves) < 2:
            return ValidationResult(valid=True, rationale="<2 moves found; abstaining")

        # Heuristic: pick the most-frequent obj as the target. Then loc1 = first
        # mention of obj; loc2 = last mention of obj that differs from loc1.
        from collections import Counter
        obj_freq = Counter(o for o, _, _ in moves).most_common(1)
        target_obj = obj_freq[0][0]
        target_moves = [(loc, pos) for o, loc, pos in moves if o == target_obj]
        if len(target_moves) < 2:
            return ValidationResult(valid=True, rationale="single move on target obj; abstaining")

        target_moves.sort(key=lambda x: x[1])
        loc1 = target_moves[0][0]      # initial / believed location
        # find last DIFFERENT location after loc1
        loc2 = None
        for loc, _ in target_moves[1:]:
            if loc != loc1:
                loc2 = loc
        if loc2 is None:
            return ValidationResult(valid=True, rationale="no different post-move location; abstaining")

        # Find which option mentions loc1 vs loc2
        opt_with_loc1 = [k for k, v in options.items() if _option_mentions(v, loc1)]
        opt_with_loc2 = [k for k, v in options.items() if _option_mentions(v, loc2)]

        if not (len(opt_with_loc1) == 1 and len(opt_with_loc2) >= 1):
            return ValidationResult(valid=True,
                rationale=f"can't disambiguate options for loc1='{loc1}' loc2='{loc2}'; abstaining")
        suggested = opt_with_loc1[0]

        if current_answer == suggested:
            return ValidationResult(valid=True,
                rationale=f"loc1='{loc1}' -> {suggested}; matches LLM")

        # The LLM picked something else (likely the loc2 option, the "actual" location)
        if current_answer in opt_with_loc2:
            return ValidationResult(
                valid=False, suggested_answer=suggested,
                feedback=f"State-backed FB check: target '{target_obj}' was at '{loc1}' "
                         f"when the asked character was last present, then was moved to '{loc2}' "
                         f"while they were absent. The character should still believe '{loc1}'. "
                         f"Option {suggested} mentions '{loc1}'; you answered {current_answer} "
                         f"(which mentions '{loc2}'). Reconsider the false-belief reasoning.",
                rationale=f"loc1='{loc1}' -> {suggested}; LLM picked {current_answer} (in loc2 set)",
            )

        # LLM picked something not loc1 or loc2 — abstain to avoid wrong substitute
        return ValidationResult(valid=True,
            rationale=f"loc1='{loc1}' -> {suggested}, but LLM={current_answer} "
                      f"isn't clearly loc1 or loc2; abstaining")
