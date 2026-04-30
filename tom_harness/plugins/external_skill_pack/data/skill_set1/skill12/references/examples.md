# HT-01 Reference

## Decision Variable

- The key variable is the hidden speech act the speaker wants the listener to recognize.

## Route Signal

- Use this skill when the literal sentence is indirect but the task asks what the speaker really means or wants.

## Hard Boundary

- If the task is about how to persuade someone, route to `skill13`.
- If the task is about nonverbal cues rather than spoken language, route to `skill7`.

## Shortcut To Avoid

- Do not paraphrase the surface wording without recovering the intended act.
- Do not answer with a broad topic label instead of the concrete requested action or recognition.

## Common Failure Modes

- Restating the sentence rather than decoding the hidden request, complaint, warning, or refusal.
- Ignoring the immediate obstacle that motivates indirectness.
- Confusing speech-act decoding with persuasion strategy selection.

## Minimal Pair

- Case A: `It's cold in here` means `please close the window` in a context with an open window.
- Case B: the same sentence remains a plain observation when no action-relevant context exists.

## Boundary Stress Test

- `What does she really mean?` -> this skill.
- `What should he say to convince her?` -> `skill13`.

## Generalization Note

- The transferable core is pragmatic inference: recover intended function from literal under-specification plus context.
