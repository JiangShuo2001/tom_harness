---
name: skill11
description: Use for SI-02 scalar update questions that revise a prior estimate after partial observation of a subset.
---

# SI-02 Scalar Update After Observation

## Use When

- The task asks for an updated quantity estimate after observing part of a set.
- The story includes both a prior scalar expectation and a later partial observation.
- The answer concerns the whole set after revision, not just the inspected subset.

## Do Not Use When

- The question is only about the prior estimate before observation. Use `skill10`.
- The task has no meaningful quantitative update step.
- The answer should be read directly from a fully observed total rather than inferred.

## Trigger Checklist

- Is there a total set size?
- Is there an initial scalar prior or expectation?
- Is there later observed evidence from part of the set?
- Is the question asking for the updated full-set estimate?
- If yes, use this skill.

## Workflow

1. Identify the total set size and the prior scalar expectation.
2. Convert the scalar prior into a rough initial count.
3. Extract the observed subset size and observed matching count.
4. Ask whether the observation supports, weakens, or overturns the prior.
5. Produce an updated estimate for the whole set, not the subset alone.
6. If options are provided, choose the option closest to the revised full-set estimate.

## Output Template

- `Task framing`: total size and after-observation status.
- `Prior`: the initial rough estimate from the scalar phrase.
- `Observed evidence`: what was seen in the subset.
- `Answer`: the updated whole-set estimate.

## Failure Checks

- Do not replace the total estimate with the observed subset count.
- Do not ignore the prior when the evidence is small or compatible with it.
- Keep before-versus-after wording explicit.
- Make sure the final answer is about the whole set.

## Boundary Exit Rule

- If no observation update is present, route to `skill10`.
- If the question is only reporting observed subset facts, do not force a whole-set estimate.
- If the task is not quantitative, route away.

## Answer Discipline

- Derive the revised whole-set estimate first, then map it to the final response or exact option.
- Prefer consistency with both prior and evidence over copying one source blindly.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
