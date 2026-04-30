"""Validators: post-LLM sanity checks that may trigger retry.

A Validator inspects the LLM's tentative answer (with full sample context)
and either:
  - approves it (.valid=True)
  - rejects it with feedback for a retry (.valid=False, .feedback="...")
  - directly substitutes a corrected answer (.suggested_answer="C")

The point of the validator layer is to catch errors that LLM self-check
cannot — the validator must use a *different signal source*:
  - procedural Python computation (e.g. recompute Scalar arithmetic)
  - structured state (e.g. belief graph consistency)
  - cross-skill agreement (sibling skill's answer)

LLM "are you sure?" self-check is NOT a validator (we tested
self-consistency at temp=0.4 — 0 lift). Don't bother.
"""

from .base import Validator, ValidationResult
from .scalar_procedural import ScalarProceduralValidator
from .cross_skill import CrossSkillValidator, DEFAULT_SIBLINGS
from .fb_state import FBStateBackedValidator

__all__ = [
    "Validator", "ValidationResult",
    "ScalarProceduralValidator",
    "CrossSkillValidator", "DEFAULT_SIBLINGS",
    "FBStateBackedValidator",
]
