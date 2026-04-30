"""Procedural handlers for skills that benefit from deterministic code.

These are registered into SkillLib via `register_handler`; the markdown
skill file still exists (so the declarative fallback and documentation are
intact), but if the handler is present SkillLib runs it instead of calling
the LLM.

Design rule: handlers accept `input_context: dict` and return a dict. They
raise on invariant violations so the executor can surface a clean failure.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# S02_quantifier_solve — arithmetic fast-path
# ─────────────────────────────────────────────────────────────────────────────

# Two calibrated mapping regimes. The "tight" one matches linguistic convention;
# the "wide" one is the fallback used by the procedural solver when the tight
# mapping produces no satisfiable solution.
QUANTIFIER_TIGHT: list[tuple[str, float, float]] = [
    # (phrase_regex, low_fraction, high_fraction)
    (r"\ball\b|全部|所有",                   1.00, 1.00),
    (r"\balmost all\b|几乎所有",              0.80, 0.95),
    (r"\bmost\b|大多数|大部分",               0.55, 0.80),
    (r"\bhalf of\b|\bhalf\b|一半",            0.45, 0.55),
    (r"\balmost half\b|几乎一半",             0.35, 0.50),
    (r"\bsome\b|一些|部分",                   0.15, 0.40),
    (r"\ba few\b|\bseveral\b|几个",           0.10, 0.25),
    (r"\bfew\b",                              0.05, 0.20),
    (r"\balmost none\b|\balmost no\b|几乎没有|几乎不", 0.00, 0.10),
    (r"\bnone\b|没有",                        0.00, 0.00),
]

QUANTIFIER_WIDE: list[tuple[str, float, float]] = [
    (r"\ball\b|全部|所有",                   1.00, 1.00),
    (r"\balmost all\b|几乎所有",              0.70, 0.95),
    (r"\bmost\b|大多数|大部分",               0.50, 0.80),
    (r"\bhalf of\b|\bhalf\b|一半",            0.40, 0.60),
    (r"\balmost half\b|几乎一半",             0.30, 0.50),
    (r"\bsome\b|一些|部分",                   0.10, 0.45),
    (r"\ba few\b|\bseveral\b|几个",           0.10, 0.30),
    (r"\bfew\b",                              0.05, 0.25),
    (r"\balmost none\b|\balmost no\b|几乎没有|几乎不", 0.00, 0.15),
    (r"\bnone\b|没有",                        0.00, 0.00),
]

_TOTAL_RE = re.compile(r"(\d+)\s*(?:items?|projects?|dishes?|个|项|道|只|个)?", re.IGNORECASE)


def _match_quantifier(phrase: str, table: list) -> tuple[float, float] | None:
    for pat, lo, hi in table:
        if re.search(pat, phrase, re.IGNORECASE):
            return (lo, hi)
    return None


def quantifier_solve(
    *,
    total: int,
    categories: dict[str, str],
    observed: dict[str, int] | None = None,
    asked: str,
    option_values: dict[str, int] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Solve for the asked category's count given quantifier phrases + observed counts.

    Parameters
    ----------
    total : int
        The total across all categories (N in the problem).
    categories : dict[str, str]
        Map `category_name -> quantifier_phrase` (e.g. {"roller_coasters": "most"}).
    observed : dict[str, int] | None
        Exact counts already known for some categories.
    asked : str
        Which category's count to return.
    option_values : dict[str, int] | None
        Map `letter -> numeric value` for each multiple-choice option; if
        supplied, the handler also returns the best option letter.

    Returns
    -------
    dict with `derived_interval`, `best_guess`, and optional `answer_letter`.
    """
    observed = observed or {}
    for regime_name, table in [("tight", QUANTIFIER_TIGHT), ("wide", QUANTIFIER_WIDE)]:
        intervals: dict[str, tuple[int, int]] = {}
        for cat, phrase in categories.items():
            iv = _match_quantifier(phrase, table)
            if iv is None:
                logger.debug(f"[S02] unrecognized quantifier: {phrase!r}")
                continue
            lo_frac, hi_frac = iv
            intervals[cat] = (int(round(lo_frac * total)),
                              int(round(hi_frac * total)))
        # Clamp by observed
        for cat, cnt in observed.items():
            if cat in intervals:
                lo, hi = intervals[cat]
                intervals[cat] = (max(lo, cnt), min(hi if hi >= cnt else cnt, total))
            else:
                intervals[cat] = (cnt, cnt)
        # Subtract to get the asked category's interval
        others = {k: v for k, v in intervals.items() if k != asked}
        if not others:
            # degenerate case
            return {
                "regime": regime_name,
                "intervals": intervals,
                "derived_interval": intervals.get(asked, (0, total)),
                "best_guess": int(round(total / 2)),
            }
        lo_others = sum(v[0] for v in others.values())
        hi_others = sum(v[1] for v in others.values())
        derived_lo = max(0, total - hi_others)
        derived_hi = min(total, total - lo_others)
        # Intersect with the asked category's own interval if present
        if asked in intervals:
            a_lo, a_hi = intervals[asked]
            derived_lo, derived_hi = max(derived_lo, a_lo), min(derived_hi, a_hi)
        if derived_lo > derived_hi:
            continue  # infeasible under this regime — retry with wider table
        midpoint = (derived_lo + derived_hi) / 2
        result = {
            "regime": regime_name,
            "intervals": intervals,
            "derived_interval": [derived_lo, derived_hi],
            "best_guess": int(round(midpoint)),
        }
        if option_values:
            in_range = {
                letter: val for letter, val in option_values.items()
                if derived_lo <= val <= derived_hi
            }
            if in_range:
                letter = min(in_range, key=lambda l: abs(in_range[l] - midpoint))
                result["answer_letter"] = letter
            else:
                letter = min(option_values, key=lambda l: abs(option_values[l] - midpoint))
                result["answer_letter"] = letter
                result["out_of_range"] = True
        return result
    # Both regimes infeasible — return best effort
    return {
        "regime": "fallback",
        "intervals": {},
        "derived_interval": [0, total],
        "best_guess": int(round(total / 2)),
        "note": "quantifier constraints infeasible; returning midpoint of total",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Handler registration
# ─────────────────────────────────────────────────────────────────────────────

PROCEDURAL_HANDLERS: dict[str, Any] = {
    "S02_quantifier_solve": quantifier_solve,
}


def register_all(skill_lib) -> int:
    """Attach every procedural handler to its SKILL.md entry.

    Called from plugins/tom/install.py after the markdown files are loaded.
    Returns the count of handlers successfully registered.
    """
    count = 0
    for skill_id, handler in PROCEDURAL_HANDLERS.items():
        existing = skill_lib.get(skill_id)
        if existing is None:
            # skill not loaded — still register a procedural-only entry
            skill_lib.register_handler(
                skill_id=skill_id,
                handler=handler,
                name=skill_id,
                description=handler.__doc__.split("\n")[0] if handler.__doc__ else "",
            )
        else:
            skill_lib.register_handler(skill_id=skill_id, handler=handler)
        count += 1
    return count
