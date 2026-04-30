# SI-01 Reference

## Decision Variable

- The key variable is how a vague scalar phrase maps to a plausible integer before any direct observation.

## Route Signal

- Use this skill when the task is prior-only estimation from a scalar phrase and a total set size.

## Hard Boundary

- If later observation must update the estimate, route to `skill11`.
- If there is no scalar-to-integer mapping problem, do not use this skill.

## Shortcut To Avoid

- Do not import later evidence into the prior estimate.
- Do not treat vague scalar language as exact arithmetic by default.

## Common Failure Modes

- Copying later observed counts into the prior.
- Ignoring the total set size.
- Treating `almost half` or `most` as if they always map to one fixed number regardless of context.

## Minimal Pair

- Case A: before inspection, estimate from scalar phrase plus total size only.
- Case B: after inspection, revise using new evidence. That belongs to `skill11`.

## Boundary Stress Test

- `Before looking, how many do you expect?` -> this skill.
- `After checking some of them, how many do you think now?` -> `skill11`.

## Generalization Note

- The transferable core is prior construction under vague language: translate approximate verbal quantity into a reasonable discrete estimate.
