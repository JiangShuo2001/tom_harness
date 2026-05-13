---
name: skill14
description: Use for SS-01 yes-no truth judgments involving mixed emotions, conflicting desires, politeness, or partial self-disclosure without collapsing the speaker into a single state.
---

# SS-01 Truth Judgment For Mixed States

## Use When

- The task asks whether a statement is true, truthful, or counts as telling the truth.
- The speaker may have mixed emotions, conflicting desires, or partial self-disclosure.
- The core issue is truth status, not motive explanation.

## Do Not Use When

- The task asks why the speaker said it. Use `skill15`.
- The task asks for direct emotion classification without a truth judgment.
- The statement is straightforward factual recall with no psychological conflict.

## Trigger Checklist

- Is the explicit task yes-no truth judgment?
- Does the story involve mixed feelings, conflict between desire and behavior, politeness, concealment, or selective truth?
- Does the answer depend on whether the statement matches any genuine part of the speaker's state?
- If yes, use this skill.

## Workflow

1. Identify the exact proposition being judged.
2. Recover the speaker's full mental state, not just one dominant feeling.
3. Ask whether the proposition matches a genuine component of that state.
4. Distinguish mixed truth, contradiction, concealment, and outright falsity.
5. Judge the proposition itself, not the entire hidden story.
6. If options are provided, map the truth judgment to the exact yes-no option.

## Output Template

- `Task framing`: the proposition to judge.
- `Mental-state evidence`: relevant feelings, desires, facts, and outward statements.
- `Reasoning decision`: whether the proposition matches a genuine part of the state.
- `Answer`: yes/no truth judgment.

## Failure Checks

- Do not mark a statement false just because the opposite feeling also exists.
- Do not call every mismatch a lie without checking for mixed state or partial truth.
- Separate truth status from motive for speaking.
- Distinguish internal conflict from deliberate deception.

## Boundary Exit Rule

- If the task asks `why did they say that`, route to `skill15`.
- If there is no truth judgment at all, do not force this skill.
- If the task is just direct emotion selection, route away.

## Answer Discipline

- Decide the proposition's truth status before thinking about motive.
- In multiple-choice settings, choose yes/no only after checking whether the proposition is genuinely satisfied by any part of the speaker's state.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
