"""Procedural handlers for skills that benefit from deterministic code.

v0.3 design principle: every skill that needs to track state uses a
Python-maintained data structure (the StoryModel), not LLM prose. The
LLM is still invoked for structured parsing/scoring, but never for
state bookkeeping.

Handlers accept `input_context: dict` and return a dict. They raise on
invariant violations so the executor can surface a clean failure.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from ..story_model import StoryModel, PARSER_SCHEMA_HINT

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
# S_build_story_model — LLM parse → Pydantic-validated StoryModel
# ─────────────────────────────────────────────────────────────────────────────

_PARSER_SYSTEM = (
    "You are a story-structure parser for a Theory-of-Mind agent. "
    "Produce a precise, conservative StoryModel JSON from the input story. "
    "Be rigorous about who observes each event — the absence of a character "
    "from a scene is load-bearing. " + PARSER_SCHEMA_HINT
)


def build_story_model(
    *,
    story: str,
    llm_fn: Callable[[str, str], str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Parse `story` into a StoryModel; Pydantic validates structural integrity."""
    if llm_fn is None:
        raise RuntimeError("S_build_story_model requires llm_fn")
    raw = llm_fn(_PARSER_SYSTEM, f"## Story\n{story}\n\n## Parse")
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    # Extract the first balanced JSON object
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError(f"no JSON object in parser response: {raw[:200]!r}")
    try:
        payload = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise ValueError(f"parser produced malformed JSON: {e}") from e
    model = StoryModel.model_validate(payload)
    return {"story_model": model.model_dump(), "n_events": len(model.events),
            "n_characters": len(model.characters)}


# ─────────────────────────────────────────────────────────────────────────────
# S_belief_query — pure Python over StoryModel (zero LLM)
# ─────────────────────────────────────────────────────────────────────────────

def belief_query(
    *,
    story_model: dict[str, Any],
    character: str,
    object: str,
    **_: Any,
) -> dict[str, Any]:
    """Return what `character` believes about `object`'s location.

    Semantics:
      - If `character` observed `object` being placed/moved → believe new location.
      - If `character` missed the move → believe the pre-move location.
      - If `character` never observed `object` → return None.
    """
    sm = StoryModel.model_validate(story_model)
    believed = sm.latest_known_location(character, object)
    actual = sm.actual_location(object)
    return {
        "character": character,
        "object": object,
        "believed_location": believed,
        "actual_location": actual,
        "has_false_belief": (believed is not None and believed != actual),
    }


# ─────────────────────────────────────────────────────────────────────────────
# S_knowledge_query — pure Python: does char know fact?
# ─────────────────────────────────────────────────────────────────────────────

def knowledge_query(
    *,
    story_model: dict[str, Any],
    character: str,
    subject: str,
    predicate: str,
    **_: Any,
) -> dict[str, Any]:
    """Does `character` know that `subject` has `predicate`?

    Returns 'yes' | 'no' | 'unknown' based on the StoryModel's declarations.
    """
    sm = StoryModel.model_validate(story_model)
    verdict = sm.character_knows(character, subject, predicate)
    return {
        "character": character,
        "subject": subject,
        "predicate": predicate,
        "verdict": verdict,
    }


# ─────────────────────────────────────────────────────────────────────────────
# S_evidence_scorer — sentence-level structured scoring
# ─────────────────────────────────────────────────────────────────────────────

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？\n])\s+")


def evidence_score(
    *,
    story: str,
    question: str,
    options: dict[str, str],
    llm_fn: Callable[[str, str], str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Score each option by textual support.

    Rather than asking the LLM to produce a free-form evidence argument,
    we:
      1. Split the story deterministically into sentences.
      2. Present the story + options to the LLM with a strict JSON
         scoring rubric: {-1, 0, 1, 2} per option.
      3. Parse and pick the highest-scoring option.
    """
    if llm_fn is None:
        raise RuntimeError("S_evidence_scorer requires llm_fn")
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(story) if s.strip()]
    numbered = "\n".join(f"[s{i}] {s}" for i, s in enumerate(sentences))
    opts_block = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    system = (
        "You are an evidence judge. Score each option by how strongly the "
        "story text supports it:\n"
        "  2 = directly stated by some sentence\n"
        "  1 = implied by a single causal step from some sentence\n"
        "  0 = requires adding unstated facts\n"
        " -1 = contradicted by the story\n"
        "Output ONLY a JSON object: "
        '{\"scores\": {\"A\": 2, \"B\": 0, ...}, \"support\": {\"A\": [\"s3\"], ...}}'
    )
    user = (
        f"## Numbered sentences\n{numbered}\n\n"
        f"## Question\n{question}\n\n"
        f"## Options\n{opts_block}\n\n"
        "## Task\nScore every option."
    )
    raw = llm_fn(system, user)
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("evidence scorer produced no JSON")
    payload = json.loads(m.group(0))
    scores: dict[str, int] = {k: int(v) for k, v in payload.get("scores", {}).items()}
    if not scores:
        raise ValueError("evidence scorer produced empty scores")
    best_letter = max(scores, key=lambda k: (scores[k], -list(scores.keys()).index(k)))
    return {
        "n_sentences": len(sentences),
        "scores": scores,
        "support": payload.get("support", {}),
        "recommendation": best_letter,
    }


# ─────────────────────────────────────────────────────────────────────────────
# S_minimal_intervention — structured rubric + Python aggregation
# ─────────────────────────────────────────────────────────────────────────────

def minimal_intervention(
    *,
    concern: str,
    options: dict[str, str],
    llm_fn: Callable[[str, str], str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Rubric-scored ranking for persuasion/advice questions.

    LLM scores each option along three dimensions on small integer scales;
    Python computes the aggregate and picks. Minimises free-form reasoning
    so the LLM cannot "argue itself into" a worse option.
    """
    if llm_fn is None:
        raise RuntimeError("S_minimal_intervention requires llm_fn")
    opts_block = "\n".join(f"{k}. {v}" for k, v in options.items() if v)
    system = (
        "Score each option on three dimensions:\n"
        "  directness [0-3]: how closely does this option address the exact concern?\n"
        "  minimality [0-3]: how little extra structure does it add?\n"
        "  politeness [0-2]: is it non-confrontational?\n"
        "Output ONLY JSON: "
        '{\"scores\": {\"A\": {\"direct\": 3, \"minimal\": 3, \"polite\": 2}, ...}}'
    )
    user = f"## Concern\n{concern}\n\n## Options\n{opts_block}\n\n## Task\nScore."
    raw = llm_fn(system, user)
    raw = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError("minimal_intervention produced no JSON")
    payload = json.loads(m.group(0))
    scored = {
        k: (2 * v.get("direct", 0) + 2 * v.get("minimal", 0) + v.get("polite", 0))
        for k, v in payload.get("scores", {}).items()
    }
    if not scored:
        raise ValueError("minimal_intervention produced empty scores")
    best = max(scored, key=lambda k: (scored[k], -list(scored.keys()).index(k)))
    return {"totals": scored, "breakdown": payload.get("scores", {}), "recommendation": best}


# ─────────────────────────────────────────────────────────────────────────────
# Handler registration
# ─────────────────────────────────────────────────────────────────────────────

PROCEDURAL_HANDLERS: dict[str, Any] = {
    "S02_quantifier_solve":   quantifier_solve,
    "S_build_story_model":    build_story_model,
    "S_belief_query":         belief_query,
    "S_knowledge_query":      knowledge_query,
    "S_evidence_scorer":      evidence_score,
    "S_minimal_intervention": minimal_intervention,
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
