---
name: skill2
description: Use for FP-02 speaker knowledge and memory questions such as Does X know or Does X remember in faux pas and social reasoning stories.
---

# FP-02 Speaker Knowledge And Memory Tracking

## Use When

- The question asks whether a person knows, does not know, remembers, or forgets a key fact.
- The task is about access to information, not about whether the remark itself was offensive.
- The answer depends on what the target person saw, heard, remembered, or missed.

## Do Not Use When

- The task asks whether a remark is socially inappropriate. Use `skill1`.
- The question asks where someone will search or what they believe about a moved object.
- The task is about indirect speech, persuasion, or emotion attribution.

## Trigger Checklist

- Is there a target fact named in the question?
- Is the real issue whether the target person had access to that fact?
- Does the story specify seeing, hearing, remembering, forgetting, absence, or surprise?
- If yes, use this skill.

## Workflow

1. Identify the exact fact whose knowledge or memory is being tested.
2. List all evidence that the target person saw it, heard it, was told it, remembered it, forgot it, or missed it.
3. Separate narrator knowledge from the character's information state.
4. Treat forgetting and missed exposure as lack of access unless the story restores the fact later.
5. Answer only from the target person's information state.
6. If options are provided, choose the option that matches the target person's actual access to the fact.

## Output Template

- `Task framing`: what fact is being tested.
- `Access evidence`: saw, heard, was told, remembered, forgot, or missed.
- `Knowledge state`: whether the target person has that fact available.
- `Answer`: yes, no, remember, or do-not-know judgment.

## Failure Checks

- Do not infer knowledge from the final social outcome.
- Treat absence and forgetting as decisive unless later corrected.
- Do not import narrator knowledge into the character's mind.
- Keep the target fact explicit all the way through the reasoning.

## Boundary Exit Rule

- If the prompt asks whether the remark itself was inappropriate, route to `skill1`.
- If the prompt asks where a person will search, route to the relevant false-belief skill.
- If no knowledge-access question is being asked, do not force this skill.

## Answer Discipline

- In multiple-choice settings, first determine the character's access status, then map it to the exact option wording.
- Prefer the option that matches the story evidence, not the socially most plausible answer.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
