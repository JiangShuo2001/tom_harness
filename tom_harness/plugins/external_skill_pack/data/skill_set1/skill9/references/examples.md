# UO-02 Reference

## Decision Variable

- The key variable is the hidden prior fact or appraisal that fully explains the reversal from expected emotion to observed emotion.

## Route Signal

- Use this skill when the prompt explicitly contrasts `should feel X` with `actually feels Y` and asks why.

## Hard Boundary

- If the task only asks which emotion the character feels, route to `skill8`.
- If no expected-versus-observed contrast is present, do not use this skill.

## Shortcut To Avoid

- Do not accept a merely plausible side story.
- Do not choose an explanation that makes the final emotion possible but fails to explain why the default emotion no longer dominates.

## Common Failure Modes

- Selecting a background fact that is loosely relevant but does not bridge the reversal.
- Explaining the visible event while ignoring the emotional shift.
- Confusing explanation mode with plain label-selection mode.

## Minimal Pair

- Case A: the hidden supportive act truly reverses disappointment into happiness.
- Case B: without that hidden act, the original disappointment remains the best explanation.

## Boundary Stress Test

- `Why is he happy instead of disappointed?` -> this skill.
- `What emotion is he feeling?` -> `skill8`.

## Generalization Note

- The transferable core is counterfactual appraisal repair: what missing fact would make the surprising emotion the rational one?
