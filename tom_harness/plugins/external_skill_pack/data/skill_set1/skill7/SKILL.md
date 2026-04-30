---
name: skill7
description: Use for AS-01 ambiguous social cue intention questions such as why someone smiled, glanced, winked, or nudged in a social scene.
---

# AS-01 Ambiguous Social Cue Intention

## Use When

- The question asks why the cue sender smiled, glanced, winked, nudged, or made a similar ambiguous cue.
- The target output is the sender's intention or social goal.
- The cue functions as shorthand for a concrete interpersonal message.

## Do Not Use When

- The question asks how another character interprets the cue. Use `skill6`.
- The task is about indirect speech from spoken language alone. Use `skill12`.
- The task is direct emotion classification rather than intention decoding.

## Trigger Checklist

- Is there a cue sender and a cue receiver?
- Is the question about why the sender performed the cue?
- Does the answer need a concrete hidden social goal rather than a mood label?
- If yes, use this skill.

## Workflow

1. Identify the cue sender, receiver, and surrounding social tension.
2. Recover the sender's local goal, concern, or coordination need.
3. Interpret the cue as shorthand for a concrete interpersonal intention.
4. Choose the option that best advances the sender's goal in that context.
5. Keep sender intention separate from observer reaction.
6. If options are provided, select the one that best captures the sender's specific goal.

## Output Template

- `Task framing`: sender, receiver, cue, and questioned intention.
- `Context evidence`: local goal, tension, or shared situation.
- `Reasoning decision`: what the sender is trying to signal or achieve.
- `Answer`: the sender's intended social meaning.

## Failure Checks

- Do not answer with the observer's reaction.
- Prefer concrete goals like warning, coordinating, teasing, reminding, or redirecting over vague mood labels.
- Use only the local social context around the cue.

## Boundary Exit Rule

- If the task asks what the observer thinks or feels after seeing the cue, route to `skill6`.
- If the task is indirect verbal meaning without a nonverbal cue, route to `skill12`.
- If no intention decoding is required, do not force this skill.

## Answer Discipline

- In multiple-choice settings, write the sender's hidden goal in plain terms first, then choose the closest option.
- Reject options that merely restate the cue without naming the intention behind it.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
