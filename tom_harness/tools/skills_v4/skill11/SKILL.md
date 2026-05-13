---
name: skill11
description: Use for SI-02 scalar update — revise a vague-quantifier prior after partial observation, enforcing the HARD SUM CONSTRAINT that all named groups sum to N.
---

# SI-02 Scalar Update After Observation

## Use When

- The task asks for an updated quantity estimate **after** observing
  part of a set.
- The story includes both a prior scalar expectation and a later
  partial observation.
- The answer concerns the whole set after revision, not just the
  inspected subset.

## Do Not Use When

- The question is only about the prior estimate before observation.
  Use `skill10`.
- The task has no meaningful quantitative update step.
- The answer should be read directly from a fully observed total
  rather than inferred.

## Trigger Checklist

- Is there a total set size N?
- Is there an initial scalar prior or expectation?
- Is there later observed evidence from part of the set?
- Is the question asking for the updated full-set estimate?
- If yes, use this skill.

## Workflow

1. Identify the total set size N and the prior scalar expectation.
2. Convert the scalar prior into a rough initial count using the TIGHT
   ranges in `skill10`.
3. Extract the observed subset size and observed matching count.
4. Apply the **HARD SUM CONSTRAINT** below to bind the estimate.
5. Produce an updated estimate for the **whole set**, not the subset
   alone.
6. If options are provided, choose the option closest to the revised
   full-set estimate.

## Detailed Procedure — TIGHT Ranges + HARD SUM CONSTRAINT

```
STEP 1 — EXTRACT
• total N (e.g. "30 seats", "40 trees", "50 lunches").
• every explicit concrete sub-count from the story
  (e.g. "4 pears", "Wang already counted 4 white").
• every scalar quantifier the speaker uses, IN ORDER. The order in
  the speaker's statement is itself a ranking signal.

STEP 2 — TIGHT QUANTIFIER RANGES (same as skill10)
  almost no X / hardly any  → 1 to 3, NOT a percentage
  a small part / a few      → 5–15% of N (smallest non-negligible)
  some                      → 15–30% of N
  almost half               → 40–48% of N
  many / a lot              → 35–55% of N
  most / the majority       → 60–85% of N (lower bound 60%, NOT 50%)
  almost all / nearly all   → 85–98% of N

STEP 3 — HARD SUM CONSTRAINT (the rule the model usually skips)
The named groups must SUM to N exactly (or to N minus any explicitly
stated "other" pool).

Procedure:
  (a) Pin "almost no X" to 1 or 2 (not its loose range).
  (b) Subtract every explicit sub-count and every "almost-no" pin
      from N. The remainder is what the larger groups must absorb.
  (c) Distribute the remainder so that the relative ranking from
      Step 1 is preserved.
  (d) If only "most" and "almost no" are mentioned, "most" absorbs
      almost the entire residual: most ≈ N − explicit − 1.

STEP 4 — DISAMBIGUATE "BEFORE" vs "AFTER" COUNTING
  • BEFORE counting → use only the quantifier range (skill10 territory)
  • AFTER counting (revealed sub-count present) → apply STEP 3 fully

STEP 5 — WORKED EXAMPLE
Story: 40 trees. "Most apples, some pears, almost no oranges. 4 pears."
Q: how many apple trees?
  • Pin oranges (almost no) → 1 (NOT 6, NOT 8).
  • Subtract: 40 − 4 (pears) − 1 (oranges) = 35.
  • Apples = 35 ✓
  • Sanity: 35/40 = 87.5%; "most" upper bound = 85%. The "almost no"
    pin forces the residual; accept it.
  ⇒ Answer = 35, NOT 30.

WORKED EXAMPLE 2 (SI-02 specifically)
Story: 15 chickens. "Almost a third are white." Wang counts a part and
finds 4 are white. Q: After counting a part, how many does he guess
are white IN TOTAL?
  • Almost a third of 15 ≈ 5 (slightly below 5 → 4 or 5).
  • The 4 he already saw is part of the white count, not the total.
  • The prior (~5) is consistent with what he has seen so far (4).
  • Updated whole-set estimate = 5.
  ⇒ Answer = 5, NOT 4 (which is just the observed subset count).
```

GUARDRAIL 1: When "almost no X" is mentioned, the residual is absorbed
by the LARGER groups. Do NOT leave a 6+ amount in the "almost no"
category just because your loose range said 25%.

GUARDRAIL 2: "most" with TIGHT pin on "almost no" can legitimately
reach 80%+ of N — accept this; do not down-weight just because the
percentage feels high.

GUARDRAIL 3: Never pick an option that equals N when another category
has a non-zero count.

GUARDRAIL 4: When two options both fit the quantifier range, prefer the
one consistent with the SUM constraint.

GUARDRAIL 5: Do NOT replace the whole-set estimate with the observed
subset count.

## Output Template

- `Task framing`: total size N and after-observation status.
- `Prior`: the initial rough estimate from the scalar phrase.
- `Observed evidence`: what was seen in the subset.
- `Reasoning decision`: how the SUM constraint and the observation
  jointly determine the whole-set estimate.
- `Answer`: the updated whole-set estimate.

## Failure Checks

- Do not replace the total estimate with the observed subset count.
- Do not ignore the prior when the evidence is small or compatible
  with it.
- Keep before-versus-after wording explicit.
- Make sure the final answer is about the whole set.

## Boundary Exit Rule

- If no observation update is present, route to `skill10`.
- If the question is only reporting observed subset facts, do not
  force a whole-set estimate.
- If the task is not quantitative, route away.

## Answer Discipline

- Derive the revised whole-set estimate first, then map it to the
  final response or exact option.
- Prefer consistency with both prior and evidence over copying one
  source blindly.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
