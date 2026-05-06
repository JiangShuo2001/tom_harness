---
name: skill10
description: Use for SI-01 scalar prior estimation — convert vague phrases like "almost half", "most", "almost no X" into the most reasonable integer estimate BEFORE any observation.
---

# SI-01 Scalar Prior Estimation (Before Observation)

## Use When

- The task asks for a quantity estimate **before** any observation
  update.
- The story gives a vague proportion phrase such as `almost half`,
  `most`, `almost one third`, `almost no X`.
- The answer must convert a scalar phrase into the most reasonable
  integer count, given a total set size.

## Do Not Use When

- The question asks for the estimate **after** observing part of the
  set. Use `skill11`.
- The task is social, emotional, or belief reasoning with no
  quantitative mapping.
- The answer should be taken directly from observed evidence rather
  than a scalar prior.

## Trigger Checklist

- Is there a total set size N?
- Is there a vague scalar phrase that must be mapped to an integer?
- Is the question about the prior state before observation?
- If yes, use this skill.

## Workflow

1. Identify the total set size N.
2. Parse the scalar phrase and decide its approximate proportion using
   the **TIGHT QUANTIFIER RANGES** below.
3. Convert that proportion into the most reasonable integer count for
   N.
4. Keep this prior separate from any later observed sample.
5. If later evidence appears but the question is still about the
   earlier state, ignore that later evidence.
6. If options are provided, choose the integer option closest to the
   scalar prior.

## Detailed Procedure — TIGHT Quantifier Ranges

These tighter ranges replace the loose textbook ranges that caused
systematic over-estimation of "almost no" and under-estimation of
"most":

```
• "almost no X" / "almost none" / "hardly any" / "very few"
      → 1 to 3 items, NOT a percentage. Treat as essentially zero.
        Even with N=100, "almost no X" should still be ≤ 5.

• "a small part" / "a small portion" / "a few"
      → 5–15% of N, AND must be the SMALLEST named non-negligible
        group.

• "some"
      → 15–30% of N.

• "almost half"
      → 40–48% of N (a hair below half).

• "many" / "a lot"
      → 35–55% of N.

• "most" / "the majority"
      → 60–85% of N. The lower bound is 60%, NOT 50%.

• "almost all" / "nearly all"
      → 85–98% of N.
```

GUARDRAIL 1: When "almost no X" is used, the count is essentially
zero — never leave a 6+ amount in that bucket no matter how large N is.

GUARDRAIL 2: "most" with TIGHT pin on "almost no" can legitimately
reach 80%+ of N — accept this; do not down-weight just because the
percentage feels high.

GUARDRAIL 3: Treat vague quantifiers as approximate, not exact.

## Output Template

- `Task framing`: total count N and before-observation status.
- `Scalar evidence`: the vague proportion phrase.
- `Reasoning decision`: how the phrase maps to a discrete prior count.
- `Answer`: the resulting integer estimate.

## Failure Checks

- Do not copy later observed counts into the prior.
- Use the total size N explicitly.
- Treat vague quantifiers as approximate, not exact.
- Keep before-versus-after wording straight.

## Boundary Exit Rule

- If the question asks for an updated estimate after seeing part of the
  set, route to `skill11`.
- If the task contains no scalar-to-integer mapping, do not force this
  skill.
- If the answer depends mainly on social inference rather than
  quantity, route away.

## Answer Discipline

- In multiple-choice settings, compute the prior count first, then
  choose the nearest matching integer option.
- Avoid options that mirror sample observations when the task is
  prior-only.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
