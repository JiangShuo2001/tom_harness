---
name: skill6
description: Use for FB-04 belief-based reaction questions where a character interprets another person's smile, glance, wink, or hint and then forms a thought or emotion.
---

# FB-04 Belief Based Reactions

## Use When

- The question asks what a target character thinks, feels, or does after observing an ambiguous social cue.
- The target character must interpret limited visible evidence.
- The output is the observer's belief-based reaction, not the cue sender's intention.

## Do Not Use When

- The question asks why the cue sender smiled, glanced, or acted. Use `skill7`.
- The task is direct emotion attribution without an ambiguous social cue.
- The answer depends on hidden narrator knowledge rather than observed behavior.

## Trigger Checklist

- Is there an observer and a socially ambiguous cue?
- Is the asked output the observer's thought, feeling, or likely response?
- Does the reasoning require `what the observer infers from what they saw`?
- If yes, use this skill.

## Workflow

1. Identify the target observer and the cue they actually perceived.
2. List only the visible evidence available to that observer.
3. Infer the belief the observer forms about the other person's intention or attitude.
4. Convert that belief into the observer's likely reaction, feeling, or action.
5. Exclude any hidden narrator facts the observer does not know.
6. If options are provided, choose the option that best matches the observer's inferred reaction.

## Output Template

- `Task framing`: observer, cue, and requested reaction target.
- `Visible evidence`: what the observer actually saw or heard.
- `Belief formation`: what the observer likely infers from that cue.
- `Answer`: the resulting reaction, emotion, or response.

## Failure Checks

- Answer from the observer's perspective only.
- Do not switch into explaining the cue sender's motive.
- Do not import narrator-level facts the observer lacks.
- Preserve suspicion, embarrassment, hurt, or confusion when the cue supports it.

## Boundary Exit Rule

- If the question is about why the cue sender acted, route to `skill7`.
- If the task is simple emotion attribution without a cue interpretation step, do not use this skill.
- If the question asks for direct indirect-speech meaning from words rather than a social cue, route to `skill12`.

## Answer Discipline

- In multiple-choice settings, infer the observer's belief first, then select the reaction option that follows from that belief.
- Avoid options that describe the sender's intention when the task asks for the observer's reaction.

## References

- For compact boundaries, minimal pairs, and common confusions, read `references/examples.md`.
