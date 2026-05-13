# SS-01 Reference

## Decision Variable

- The key variable is whether the proposition matches any genuine component of the speaker's current state.

## Route Signal

- Use this skill when the task explicitly asks whether a statement is true, truthful, or counts as telling the truth.

## Hard Boundary

- If the task asks why the speaker said it, route to `skill15`.
- If there is no truth judgment and the task is just emotion labeling, do not use this skill.

## Shortcut To Avoid

- Do not collapse the speaker into one positive or negative feeling.
- Do not treat every inner conflict as a lie.

## Common Failure Modes

- Marking a statement false just because an opposite feeling also exists.
- Confusing selective truth with outright falsity.
- Answering the motive question when the actual task is truth status.

## Minimal Pair

- Case A: one side of a mixed state can be genuinely true.
- Case B: a statement is false when it denies a desire, feeling, or fact that is not genuinely satisfied.

## Boundary Stress Test

- `Is what he says true?` -> this skill.
- `Why does he say that?` -> `skill15`.

## Generalization Note

- The transferable core is proposition-level evaluation under mixed mental states: truth is judged against the statement itself, not against a simplified one-emotion summary.
