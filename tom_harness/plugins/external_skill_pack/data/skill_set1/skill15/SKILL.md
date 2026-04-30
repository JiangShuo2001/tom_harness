---
name: skill15
description: Use for SS-02 why-did-they-say-that questions when a statement is false, partial, polite, self-protective, forgetful, ironic, or otherwise nonliteral.
---

# SS-02 Motive Explanation For Nonliteral Statements

## Use When

- The task asks why a speaker said something that is false, partial, selective, polite, self-protective, mistaken, or otherwise nonliteral.
- The target output is the speaker's motive, not the statement's truth status.
- The story requires distinguishing memory failure, face-saving, politeness, concealment, self-interest, and conflict avoidance.

## Do Not Use When

- The task only asks whether the statement is true. Use `skill14`.
- The task is persuasion, hinting, or direct emotion classification.
- There is no nonliteral or selective statement to explain.

## Trigger Checklist

- Is there a specific statement whose motive must be explained?
- Does the statement depart from plain factual reporting or full disclosure?
- Does the story provide pressure, goal, relationship, or memory-state clues that explain the wording choice?
- If yes, use this skill.

## Workflow

1. Identify the statement and how it departs from plain factual reporting.
2. Classify the deviation: forgetting, confusion, white lie, egocentric lie, conflict avoidance, face-saving, selective truth, irony, or mixed emotion.
3. Recover the speaker's immediate goal or pressure.
4. Choose the explanation that best links the motive to the social context.
5. Keep `truth status` separate from `motive for saying it`.
6. If options are provided, pick the option that best explains why the speaker used that wording.

## Output Template

- `Task framing`: statement and type of nonliteral deviation.
- `Motive evidence`: pressure, goal, relationship, memory state, or self-protection cue.
- `Reasoning decision`: why the speaker chose that wording.
- `Answer`: the best motive explanation.

## Failure Checks

- Do not call every mismatch a deliberate lie.
- Distinguish forgetting from deception.
- Explain the motive for saying it, not just the objective facts.
- Separate social face-saving from factual confusion.

## Boundary Exit Rule

- If the task only asks whether the statement is true, route to `skill14`.
- If there is no statement motive to explain, do not force this skill.
- If the task is persuasion strategy or indirect-speech decoding, route to the appropriate skill instead.

## Answer Discipline

- Name the deviation type first, then choose the answer that best fits the speaker's local goal.
- Reject options that merely restate the hidden facts without explaining why that wording was chosen.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
