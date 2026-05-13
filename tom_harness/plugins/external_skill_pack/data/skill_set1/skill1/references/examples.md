# FP-01 Reference

## Decision Variable

- The key variable is whether a spoken line makes a sensitive fact socially harmful in that moment.

## Route Signal

- Use this skill when the question targets the remark itself: `Was that inappropriate?` or `Which sentence was wrong to say?`

## Hard Boundary

- If the question asks whether the speaker knew, remembered, or forgot the fact, route to `skill2`.
- If there is no spoken line to evaluate, do not use this skill.

## Shortcut To Avoid

- Do not label a line as faux pas just because it is negative, awkward, or blunt.
- Do not solve by keyword matching without checking social harm.

## Common Failure Modes

- Confusing social inappropriateness with factual error.
- Returning a paraphrase instead of the exact offending sentence.
- Smuggling in the speaker-knowledge question when the prompt only asks about the remark.

## Minimal Pair

- Case A: a negative remark with no sensitive fact is blunt but not necessarily a faux pas.
- Case B: a mild-looking remark that exposes a painful fact is a faux pas.

## Boundary Stress Test

- `Did he know her grandmother had died?` -> `skill2`, not this skill.
- `Which sentence was inappropriate?` -> this skill.

## Generalization Note

- The transferable core is social-harm detection from dialogue context: identify when a spoken line exposes a sensitive fact in a way that embarrasses or hurts the listener.
