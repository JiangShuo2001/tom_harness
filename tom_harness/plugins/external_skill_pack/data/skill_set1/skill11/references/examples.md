# SI-02 Reference

## Decision Variable

- The key variable is how partial evidence should revise a prior estimate for the whole set.

## Route Signal

- Use this skill when the task combines an initial scalar prior with later observed evidence and asks for an updated whole-set estimate.

## Hard Boundary

- If the question is prior-only and no update is required, route to `skill10`.
- If the task only asks about the observed subset itself, do not force a whole-set update.

## Shortcut To Avoid

- Do not replace the whole-set estimate with the observed subset count.
- Do not ignore the prior when the evidence is small or compatible with it.

## Common Failure Modes

- Confusing subset evidence with total-set estimate.
- Repeating the prior without checking whether the new evidence should move it.
- Losing track of before-versus-after wording.

## Minimal Pair

- Case A: the observed sample supports the prior, so the update stays nearby.
- Case B: the observed sample conflicts strongly with the prior, so the update shifts more.

## Boundary Stress Test

- `After checking some of them, what is your estimate now?` -> this skill.
- `Before checking any, what do you expect?` -> `skill10`.

## Generalization Note

- The transferable core is belief revision under partial evidence: integrate prior expectation with new sample information rather than copying either source blindly.
