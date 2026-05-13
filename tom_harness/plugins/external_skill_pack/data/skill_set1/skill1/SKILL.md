---
name: skill1
description: Use for FP-01 faux pas detection questions that ask whether anyone said something inappropriate or which sentence is inappropriate in a social story.
---

# FP-01 Faux Pas Detection

## Use When

- The task asks whether anyone said something inappropriate, awkward, rude, or hurtful.
- The task asks which sentence or remark is the faux pas.
- The core target is the remark itself, not the speaker's knowledge state.

## Do Not Use When

- The task asks whether the speaker knew, remembered, or forgot the hidden fact. Use `skill2`.
- The task is about indirect meaning, persuasion, false belief, or emotion selection.
- The story contains hurt feelings, but the question is not about the appropriateness of a spoken line.

## Trigger Checklist

- Is there a spoken line to evaluate?
- Does the line touch a sensitive fact, hidden failure, private loss, illness, secret, or embarrassment?
- Does the question ask whether that remark itself is socially inappropriate?
- If yes, use this skill. If the question instead asks what the speaker knew, route to `skill2`.

## Workflow

1. Extract the exact spoken lines.
2. Mark any line that highlights a sensitive fact, painful contrast, or private problem.
3. Check whether saying that line aloud would hurt, embarrass, or put the listener on the spot in that moment.
4. Separate `Was the line socially inappropriate?` from `Did the speaker know enough for it to count as a faux pas?`
5. Answer only the question that was asked. If the task asks for the offending sentence, return the exact line, not a paraphrase.
6. If options are provided, map the identified offending line to the exact option text.

## Output Template

- `Task framing`: yes-no faux-pas detection or exact sentence selection.
- `Sensitive fact`: what painful fact is being exposed.
- `Social harm`: why saying it aloud is awkward or hurtful here.
- `Answer`: the exact offending line, or a no-faux-pas judgment.

## Failure Checks

- Do not mark a line as faux pas just because it is negative or blunt.
- Do not answer the speaker-knowledge question inside this skill unless the prompt explicitly asks for it.
- Prefer context-based social harm over keyword matching.
- Return the exact sentence when the task asks which remark was inappropriate.

## Boundary Exit Rule

- If the question is `Did X know`, `Did X remember`, or `Was X aware`, stop and use `skill2`.
- If there is no spoken remark to judge, do not force this skill.
- If the task is really about intention, hinting, or belief tracking, route to the corresponding skill instead of staying in faux-pas mode.

## Answer Discipline

- In multiple-choice settings, identify the offending remark in free reasoning first, then choose the exact matching option.
- Do not choose an option that is merely similar in tone; choose the line that creates the actual social mistake.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
