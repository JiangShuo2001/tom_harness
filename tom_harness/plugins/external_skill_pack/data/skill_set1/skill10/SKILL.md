---
name: skill10
description: Use for SI-01 scalar prior estimation questions that convert phrases like almost half or almost one third into the most reasonable integer estimate before observation.
---

# SI-01 Scalar Prior Estimation

## Use When

- The task asks for a quantity estimate before any observation update.
- The story gives a vague proportion phrase such as `almost half`, `most`, or `almost one third`.
- The answer must convert a scalar phrase into the most reasonable integer count.

## Do Not Use When

- The question asks for the estimate after observing part of the set. Use `skill11`.
- The task is social, emotional, or belief reasoning with no quantitative mapping.
- The answer should be taken directly from observed evidence rather than a scalar prior.

## Trigger Checklist

- Is there a total set size?
- Is there a vague scalar phrase that must be mapped to an integer?
- Is the question about the prior state before observation?
- If yes, use this skill.

## Workflow

1. Identify the total set size.
2. Parse the scalar phrase and decide its approximate proportion.
3. Convert that proportion into the most reasonable integer count for the total size.
4. Keep this prior separate from any later observed sample.
5. If later evidence appears but the question is still about the earlier state, ignore that later evidence.
6. If options are provided, choose the integer option closest to the scalar prior.

## Output Template

- `Task framing`: total count and before-observation status.
- `Scalar evidence`: the vague proportion phrase.
- `Reasoning decision`: how the phrase maps to a discrete prior count.
- `Answer`: the resulting integer estimate.

## Failure Checks

- Do not copy later observed counts into the prior.
- Use the total size explicitly.
- Treat vague quantifiers as approximate, not exact.
- Keep before-versus-after wording straight.

## Boundary Exit Rule

- If the question asks for an updated estimate after seeing part of the set, route to `skill11`.
- If the task contains no scalar-to-integer mapping, do not force this skill.
- If the answer depends mainly on social inference rather than quantity, route away.

## Answer Discipline

- In multiple-choice settings, compute the prior count first, then choose the nearest matching integer option.
- Avoid options that mirror sample observations when the task is prior-only.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
