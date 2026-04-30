"""Scalar Implicature procedural validator.

For ToMBench Scalar Implicature problems:
  - Story states a total set size N (e.g. "18 players")
  - Story uses a vague proportion phrase (e.g. "almost one third")
  - Story (often) gives an observed count (e.g. "found 4 goalkeepers")
  - Question asks for one of: prior, observed-now, remaining, total

We extract (N, fraction, observed) from the story with deterministic
regex, compute the integer answer in Python, then map it to the option
letter. If the LLM's answer disagrees with what arithmetic says, we
either substitute the procedural answer directly or ask the LLM to
retry with the computation explicitly stated.

This is the prototype of "harness > pure skills" — pure skills can
only nudge the LLM via prompt; this validator literally computes the
right answer when possible. Cost: 0 LLM calls.

NOTE: this is intentionally narrow. It only fires when (N, fraction,
observed) can all be parsed; otherwise it abstains (`valid=True` to
not block).
"""

from __future__ import annotations

import re

from .base import Validator, ValidationResult


# ── parsers ─────────────────────────────────────────────────────────────────
# `18 players`, `12 students`, `30 cars`
_TOTAL_RE = re.compile(r"\b(\d+)\s+(?:players|students|people|workers|kids|children|cars|fans|guests|members|customers|visitors|tourists|cats|dogs|animals|seats|books|apples|cookies|eggs|fish|bottles|cups|coins|cards|fish|chairs|pieces|items|balls|fruits)\b", re.IGNORECASE)

# "almost half", "almost one third", "almost one quarter", "most", "more than half"
_FRACTION_PATTERNS: list[tuple[re.Pattern[str], float, str]] = [
    (re.compile(r"\balmost\s+half\b", re.I),                   0.5,    "almost"),
    (re.compile(r"\balmost\s+one[-\s]+third\b", re.I),         1/3,    "almost"),
    (re.compile(r"\balmost\s+one[-\s]+quarter\b", re.I),       0.25,   "almost"),
    (re.compile(r"\balmost\s+three[-\s]+quarters\b", re.I),    0.75,   "almost"),
    (re.compile(r"\balmost\s+two[-\s]+thirds\b", re.I),        2/3,    "almost"),
    (re.compile(r"\bmore\s+than\s+half\b", re.I),              0.5,    "more_than"),
    (re.compile(r"\bless\s+than\s+half\b", re.I),              0.5,    "less_than"),
    (re.compile(r"\bmost\b", re.I),                            0.7,    "most"),     # heuristic
    (re.compile(r"\b(?:one[-\s]+)?half\b", re.I),              0.5,    "exact"),
    (re.compile(r"\bone[-\s]+third\b", re.I),                  1/3,    "exact"),
    (re.compile(r"\bone[-\s]+quarter\b", re.I),                0.25,   "exact"),
]

# `find 4`, `finds 4 goalkeepers`, `there are 4 ... already`
_OBSERVED_RE = re.compile(r"\b(?:finds?|find|sees?|see|count(?:s|ed)?|gets?|get|already)\b[^.]{0,40}?\b(\d+)\b", re.IGNORECASE)

_QUESTION_KIND_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bbefore\b.+\bhow many\b", re.I),                          "prior"),
    (re.compile(r"\bafter\b.+\bhow many.+(?:remain|left|still)", re.I),      "remaining"),
    (re.compile(r"\bhow many\b.+\b(?:remain|left|still)", re.I),             "remaining"),
    (re.compile(r"\b(?:in total|total|altogether)\b", re.I),                 "total"),
]


def _round_for_quantifier(value: float, qualifier: str) -> int:
    """Map a real number to the integer count implied by the qualifier.

    'almost X'  -> strictly less than X. If the math gives an exact
                   integer (e.g. 18 * 1/3 = 6.0), return X-1 (= 5).
                   Otherwise floor.
    'more_than' -> strictly greater. Exact int -> +1, else ceil.
    'less_than' -> strictly less. Exact int -> -1, else floor.
    'most'      -> heuristic round (we use 0.7 fraction in the table).
    'exact'/default -> nearest int.
    """
    import math
    is_exact = abs(value - round(value)) < 1e-6
    if qualifier == "almost":
        return max(0, int(round(value)) - 1) if is_exact else int(math.floor(value))
    if qualifier == "more_than":
        return int(round(value)) + 1 if is_exact else int(math.ceil(value))
    if qualifier == "less_than":
        return max(0, int(round(value)) - 1) if is_exact else int(math.floor(value))
    return int(round(value))


def _extract_int_from_option_text(opt_text: str) -> int | None:
    """Pull the first integer from an option string."""
    m = re.search(r"\b(\d+)\b", opt_text or "")
    return int(m.group(1)) if m else None


def _classify_question(question: str) -> str | None:
    for pat, kind in _QUESTION_KIND_PATTERNS:
        if pat.search(question):
            return kind
    return None


def _parse_scalar_facts(story: str) -> tuple[int | None, float | None, str | None, int | None]:
    """Return (total, fraction, qualifier, observed) — any may be None on miss."""
    total_m = _TOTAL_RE.search(story)
    total = int(total_m.group(1)) if total_m else None

    fraction = None; qualifier = None
    for pat, frac, q in _FRACTION_PATTERNS:
        if pat.search(story):
            fraction = frac; qualifier = q
            break

    observed = None
    obs_m = _OBSERVED_RE.search(story)
    if obs_m:
        observed = int(obs_m.group(1))

    return total, fraction, qualifier, observed


class ScalarProceduralValidator(Validator):
    """Recompute Scalar arithmetic and check / correct LLM answer.

    Suggests a directly-substituted answer when the procedural number
    matches exactly one option; otherwise abstains.
    """

    applies_to_tasks: set[str] = {"Scalar Implicature Test"}

    def validate(
        self,
        *,
        question: str,
        story: str,
        options: dict[str, str],
        task_type: str | None,
        current_answer: str,
    ) -> ValidationResult:
        total, fraction, qualifier, observed = _parse_scalar_facts(story)
        kind = _classify_question(question)

        if total is None or fraction is None or kind is None:
            # can't compute — abstain (valid=True so we don't block)
            return ValidationResult(valid=True, rationale="scalar facts not parseable; abstaining")

        prior = _round_for_quantifier(total * fraction, qualifier or "exact")
        if kind == "prior":
            target = prior
        elif kind == "remaining" and observed is not None:
            target = max(0, prior - observed)
        elif kind == "total":
            target = total
        else:
            return ValidationResult(valid=True, rationale=f"kind={kind} but missing observed")

        # Find option whose integer matches target
        matching: list[str] = []
        for letter, opt_text in options.items():
            opt_int = _extract_int_from_option_text(opt_text)
            if opt_int == target:
                matching.append(letter)

        if len(matching) != 1:
            return ValidationResult(valid=True,
                rationale=f"computed={target} but {len(matching)} options match; abstaining")

        suggested = matching[0]
        if suggested == current_answer:
            return ValidationResult(valid=True,
                rationale=f"procedural={target} -> {suggested} (matches LLM)")

        # Disagreement: substitute
        return ValidationResult(
            valid=False,
            suggested_answer=suggested,
            feedback=f"Procedural arithmetic: total={total}, fraction={fraction:.3f} ({qualifier}), "
                     f"observed={observed}, kind={kind}, computed={target}. "
                     f"The integer {target} appears in option {suggested}. "
                     f"You answered {current_answer}; reconsider with explicit calculation.",
            rationale=f"procedural={target} -> {suggested} (LLM said {current_answer})",
        )
