---
name: micro-15
level: micro
layer: L2
family: "belief-models"
description: "Diagnose how the arrival of new evidence changes a character's belief, without judging the source itself."
---

# Evidence-Availability Updating

## Use When
- Use when the question asks how newly available information changes what someone believes.
- Use when the task is to determine the direction of belief update after new evidence appears, is revealed, or becomes noticed.
- Use when the key issue is whether the character now believes more, believes less, or revises a prior assumption because of fresh evidence.

## Do Not Use When
- Do not use when the main issue is whether the evidence source is credible, deceptive, or trustworthy; that is a source-evaluation problem, not an update-direction problem.
- Do not use when the question asks what one person thinks another person thinks; use recursive belief instead.
- Do not use when the task is about common knowledge, certainty level, or appearance versus reality rather than the effect of new evidence.
- Do not use when no new fact, observation, or disclosure has arrived; without a fresh input there is no update direction to compute.

## Decision Variable
the direction of belief change caused by newly available evidence

## Trigger Checklist
- A new fact, clue, observation, disclosure, or reminder becomes available.
- The question asks what belief changes, not whether the source is honest.
- The answer depends on whether the new evidence supports, weakens, or leaves unchanged a prior belief.
- The scene is about update effect, not deeper reasoning about who knows what.

## Workflow
- Identify the prior belief before the new evidence appears.
- Identify the new evidence and whether it is now visible, known, or disclosed.
- Compare the evidence to the prior belief and judge the update direction: strengthen, weaken, or no change.
- Ignore source credibility unless the prompt explicitly makes credibility the main issue.

## Special Case
**New evidence is relevant but not decisive**: If the new information only weakly supports the prior belief, answer by the direction of partial updating, not by certainty or truth status.

Scene: A friend thinks it may rain. She sees dark clouds, but no rain has started yet.
Question: How should her belief change?
Answer logic: The clouds are newly available evidence that increases the probability of rain, so the belief should update in the positive direction even though the conclusion is not certain.

## Boundary Exit Rule
- Exit to micro-18 if the question is about whether the information source is reliable, misleading, or lying.
- Exit to micro-13 if the central issue is one mind representing another mind's belief state.
- Exit to micro-16 or micro-17 if the prompt asks about certainty, guessing, or shared/public knowledge rather than update direction.
- Exit to micro-14 if the task is about what is really true in the world, not how belief shifts from new evidence.

## References
- See `references/examples.md` for route signals, hard boundaries, and minimal pairs.

## Quick Route Signal
Use this micro unit when a case asks how a new observation or disclosure changes belief, and the main output is the direction of the update.
