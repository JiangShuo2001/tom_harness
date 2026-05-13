---
name: skill8
description: Use for UO-01 atypical emotion attribution when character traits, prior goals, or unusual context override the default everyday emotional script.
---

# UO-01 Atypical Emotion Attribution

## Use When

- The question asks what emotion a character has or shows.
- The obvious default everyday emotion may be wrong.
- A trait, prior goal, relationship, value, or hidden appraisal changes the default script.

## Do Not Use When

- The question asks why a surprising emotion happened. Use `skill9`.
- The task is mixed-emotion truth judgment or statement truthfulness. Use `skill14`.
- The story contains no meaningful override and only asks for a standard typical reaction.

## Trigger Checklist

- Does the story invite an obvious default emotion?
- Is there a character-specific override such as bravery, guilt, prior arrangement, role obligation, or moral appraisal?
- Is the question asking `which emotion`, not `why this emotion`?
- If yes, use this skill.

## Workflow

1. Write down the default emotion an average person might feel.
2. Search for override cues: character trait, prior goal, value conflict, relationship history, social norm, or self-appraisal.
3. Recompute the emotion from the character's specific appraisal, not from the generic script.
4. Prefer the narrower social emotion if it better explains the override.
5. If the task is really asking for the hidden cause of the reversal, stop and route to `skill9`.
6. If options are provided, pick the option that best reflects the overridden appraisal.

## Output Template

- `Task framing`: character, event, and default expected emotion.
- `Override evidence`: trait, goal, relationship, or self-appraisal cue.
- `Reasoning decision`: why the default script is overridden.
- `Answer`: the final overridden emotion.

## Failure Checks

- Do not answer from average-person intuition alone.
- Check override cues before committing to fear, anger, sadness, or happiness.
- Consider narrower emotions such as guilt, regret, embarrassment, disgust, curiosity, relief, or worry.
- Separate emotion selection from hidden-cause explanation.

## Boundary Exit Rule

- If the prompt says `should feel X but instead feels Y, why`, route to `skill9`.
- If the task is about truth status of a statement, route to `skill14`.
- If there is no override cue at all, do not force atypical-emotion reasoning.

## Answer Discipline

- In multiple-choice settings, name the default emotion first, then check which option is best supported by the override evidence.
- Reject broad but generic options when a narrower override emotion is clearly licensed.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
