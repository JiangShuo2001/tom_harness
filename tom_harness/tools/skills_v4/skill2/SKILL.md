---
name: skill2
description: Use for FP-02 speaker knowledge and memory questions — "Does X know?", "Does X remember?", "Did X forget?" — by tracking each character's perception ledger of who saw or heard what.
---

# FP-02 Speaker Knowledge and Memory Tracking

## Use When

- The question asks whether a person knows, does not know, remembers,
  or forgets a key fact.
- The task is about access to information, not about whether the remark
  itself was offensive.
- The answer depends on what the target person saw, heard, remembered,
  or missed.

## Do Not Use When

- The task asks whether a remark is socially inappropriate. Use
  `skill1`.
- The question asks where someone will *search* for a moved object or
  what they *believe* about a moved object — that's a downstream use of
  knowledge tracking and is handled by `skill3` / `skill4` / `skill5`.
- The task is about indirect speech, persuasion, or emotion attribution.

## Trigger Checklist

- Is there a target fact named in the question?
- Is the real issue whether the target person had access to that fact?
- Does the story specify seeing, hearing, remembering, forgetting,
  absence, or surprise?
- If yes, use this skill.

## Workflow

1. Identify the exact fact whose knowledge or memory is being tested.
2. List all evidence that the target person saw it, heard it, was told
   it, remembered it, forgot it, or missed it.
3. Separate **narrator knowledge** from the **character's information
   state**.
4. Treat forgetting and missed exposure as lack of access unless the
   story restores the fact later.
5. Answer only from the target person's information state.
6. If options are provided, choose the option that matches the target
   person's actual access to the fact.

## Detailed Procedure — Perception Ledger (one-step version)

For the target character only, list every event in the story that could
have conveyed the asked fact:

| Event | Was target present? | Sensory channel available? | Was the fact stated explicitly to them? |
|---|---|---|---|

Then:

- **YES they know** = at least one row has all three columns checked
  AND no later event explicitly states they forgot.
- **NO they don't know** = no row satisfies the three columns.
- **They forgot** = a YES row exists but a later sentence explicitly
  states forgetting / time gap / "didn't recall".

Default: a character only knows what they personally witnessed (eyes,
ears, were-told). The narrator's omniscient view does not transfer.

## Output Template

- `Task framing`: what fact is being tested.
- `Access evidence`: saw, heard, was told, remembered, forgot, or
  missed.
- `Knowledge state`: whether the target person has that fact available.
- `Answer`: yes, no, remember, or do-not-know judgment, mapped to the
  exact option text if needed.

## Failure Checks

- Do not infer knowledge from the final social outcome.
- Treat absence and forgetting as decisive unless later corrected.
- Do not import narrator knowledge into the character's mind.
- Keep the target fact explicit all the way through the reasoning.

## Boundary Exit Rule

- If the prompt asks whether the remark itself was inappropriate, route
  to `skill1`.
- If the prompt asks where a person will search or what they expect to
  find, route to the false-belief skills (`skill3` / `skill4` /
  `skill5`).
- If no knowledge-access question is being asked, do not force this
  skill.

## Answer Discipline

- In multiple-choice settings, first determine the character's access
  status, then map it to the exact option wording.
- Prefer the option that matches the story evidence, not the socially
  most plausible answer.

## References

- For compact boundaries, minimal pairs, and common confusions, read
  `references/examples.md`.
- The full character-knowledge ledger procedure (used recursively for
  belief skills `skill3`–`skill5`) lives in `skill3/SKILL.md`.
